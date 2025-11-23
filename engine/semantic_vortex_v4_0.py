"""Voynich OS — Semantic Vortex Engine v4.0R

Safe, deterministic semantic vortex field for Voynich OS.

Purpose
-------
This is a **rebuild** engine for v4.0, designed to safely reconstruct
the required file:

  • data/meaning_v4_0/semantic_vortex_v4_0.json

(and a compact companion map:)

  • data/meaning_v4_0/vortex_bands_v4_0.json

from existing, already-computed weather data:

  • data/meaning_v3_9/semantic_weather_v3_9.json

It produces stable, analytic JSON structures that are:
  • Deterministic
  • Non-adaptive
  • Purely analytic (no learning, no randomness)

The structure is designed to be robust and compatible with downstream
engines (v4.1 / v4.2), following the same defensive .get() + defaults
pattern used in v3.7–v3.9.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone


REPO_ROOT = Path(__file__).resolve().parents[1]

MEANING_V39 = REPO_ROOT / "data" / "meaning_v3_9"
OUTDIR      = REPO_ROOT / "data" / "meaning_v4_0"

SEMANTIC_WEATHER = MEANING_V39 / "semantic_weather_v3_9.json"

SEMANTIC_VORTEX = OUTDIR / "semantic_vortex_v4_0.json"
VORTEX_BANDS    = OUTDIR / "vortex_bands_v4_0.json"


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def _safe_float(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


def _safe_int(x: Any) -> int:
    try:
        return int(x)
    except Exception:
        return 0


def _normalize(x: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    v = (x - lo) / (hi - lo)
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


# ────────────────────────────────────────────────────────────────────
# Core vortex builders (analytic, no learning)
# ────────────────────────────────────────────────────────────────────

def _compute_global_ranges(per_folio: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    fields = ["continuity_avg", "local_theme_pressure", "local_motif_density",
              "storm_index", "stability_index", "volatility_index"]
    stats: Dict[str, Dict[str, float]] = {}

    for field in fields:
        values = [_safe_float(f.get(field)) for f in per_folio]
        values = [v for v in values if v != 0.0]  # ignore exact zeros to avoid noise
        if not values:
            stats[field] = {"min": 0.0, "max": 1.0, "avg": 0.0}
        else:
            mn = min(values)
            mx = max(values)
            av = sum(values) / float(len(values))
            stats[field] = {"min": mn, "max": mx, "avg": av}

    return stats


def build_semantic_vortex(weather: Dict[str, Any]) -> Dict[str, Any]:
    """Build semantic vortex field from v3.9 per-folio weather."""
    per_folio_raw = weather.get("per_folio", []) if isinstance(weather, dict) else []
    per_folio_raw = [f for f in per_folio_raw if isinstance(f, dict)]

    ranges = _compute_global_ranges(per_folio_raw)
    cont_r = ranges["continuity_avg"]
    press_r = ranges["local_theme_pressure"]
    storm_r = ranges["storm_index"]
    stab_r = ranges["stability_index"]
    vol_r = ranges["volatility_index"]

    vortex_entries: List[Dict[str, Any]] = []

    for f in per_folio_raw:
        fid = f.get("folio_id")
        if not fid:
            continue

        cont = _safe_float(f.get("continuity_avg"))
        press = _safe_float(f.get("local_theme_pressure"))
        dens = _safe_float(f.get("local_motif_density"))
        storm = _safe_float(f.get("storm_index"))
        stab = _safe_float(f.get("stability_index"))
        vol = _safe_float(f.get("volatility_index"))
        drift = _safe_float(f.get("drift_index"))

        cont_n = _normalize(cont, cont_r["min"], cont_r["max"])
        press_n = _normalize(press, press_r["min"], press_r["max"])
        storm_n = _normalize(storm, storm_r["min"], storm_r["max"])
        stab_n = _normalize(stab, stab_r["min"], stab_r["max"])
        vol_n = _normalize(vol, vol_r["min"], vol_r["max"])

        # Vortex index: where high storm + volatility overpower stability
        vortex_index = max(0.0, storm_n * (0.6 + 0.4 * vol_n) - 0.5 * stab_n)

        # Still-point index: high stability, low storm, moderate pressure
        still_index = max(0.0, stab_n * (1.0 - 0.5 * storm_n))

        # Shear index: where pressure and continuity gradients have been strong
        # (we approximate via volatility + difference between press_n and cont_n)
        shear_index = max(0.0, abs(press_n - cont_n) * (0.5 + 0.5 * vol_n))

        # Category (deterministic)
        if vortex_index >= 0.65:
            band = "vortex_core"
        elif vortex_index >= 0.40:
            band = "vortex_shear"
        elif still_index >= 0.65:
            band = "still_point"
        elif shear_index >= 0.45:
            band = "transition_ridge"
        else:
            band = "background_flow"

        vortex_entries.append(
            {
                "folio_id": fid,
                "dominant_theme": f.get("dominant_theme"),
                "category_prev": f.get("category"),
                "continuity_avg": cont,
                "local_theme_pressure": press,
                "local_motif_density": dens,
                "storm_index": storm,
                "stability_index": stab,
                "volatility_index": vol,
                "drift_index": drift,
                "continuity_norm": cont_n,
                "pressure_norm": press_n,
                "storm_norm": storm_n,
                "stability_norm": stab_n,
                "vortex_index": vortex_index,
                "still_point_index": still_index,
                "shear_index": shear_index,
                "vortex_band": band,
            }
        )

    # Global stats for the vortex field
    if vortex_entries:
        v_vals = [e["vortex_index"] for e in vortex_entries]
        s_vals = [e["still_point_index"] for e in vortex_entries]
        sh_vals = [e["shear_index"] for e in vortex_entries]

        vortex_stats = {
            "vortex_index": {
                "min": min(v_vals),
                "max": max(v_vals),
                "avg": sum(v_vals) / float(len(v_vals)),
            },
            "still_point_index": {
                "min": min(s_vals),
                "max": max(s_vals),
                "avg": sum(s_vals) / float(len(s_vals)),
            },
            "shear_index": {
                "min": min(sh_vals),
                "max": max(sh_vals),
                "avg": sum(sh_vals) / float(len(sh_vals)),
            },
        }
    else:
        vortex_stats = {
            "vortex_index": {"min": 0.0, "max": 0.0, "avg": 0.0},
            "still_point_index": {"min": 0.0, "max": 0.0, "avg": 0.0},
            "shear_index": {"min": 0.0, "max": 0.0, "avg": 0.0},
        }

    return {
        "meta": {
            "version": "4.0R",
            "description": "Rebuilt semantic vortex field from v3.9 weather.",
            "source_weather_file": str(SEMANTIC_WEATHER),
        },
        "per_folio": vortex_entries,
        "vortex_stats": vortex_stats,
    }


def build_vortex_bands(semantic_vortex: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize vortex bands (core / shear / still / transition / background)."""
    entries = semantic_vortex.get("per_folio", []) if isinstance(semantic_vortex, dict) else []
    bands: Dict[str, Dict[str, Any]] = {}

    for e in entries:
        band = str(e.get("vortex_band") or "background_flow")
        rec = bands.setdefault(
            band,
            {
                "band": band,
                "num_folios": 0,
                "sum_vortex": 0.0,
                "sum_still": 0.0,
                "sum_shear": 0.0,
            },
        )
        rec["num_folios"] += 1
        rec["sum_vortex"] += _safe_float(e.get("vortex_index"))
        rec["sum_still"] += _safe_float(e.get("still_point_index"))
        rec["sum_shear"] += _safe_float(e.get("shear_index"))

    band_list: List[Dict[str, Any]] = []
    for band, rec in bands.items():
        n = rec["num_folios"] or 1
        band_list.append(
            {
                "band": band,
                "num_folios": rec["num_folios"],
                "avg_vortex_index": rec["sum_vortex"] / float(n),
                "avg_still_point_index": rec["sum_still"] / float(n),
                "avg_shear_index": rec["sum_shear"] / float(n),
            }
        )

    # Sort: cores first, then shear, then still, then others
    order = {"vortex_core": 0, "vortex_shear": 1, "still_point": 2, "transition_ridge": 3}
    band_list.sort(key=lambda b: order.get(b["band"], 99))

    return {
        "meta": {
            "version": "4.0R",
            "description": "Band-level summary of semantic vortex field.",
        },
        "bands": band_list,
    }


# ────────────────────────────────────────────────────────────────────
# Pipeline
# ────────────────────────────────────────────────────────────────────

def run_v4_0R_pipeline() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    weather = _load_json(SEMANTIC_WEATHER)
    semantic_vortex = build_semantic_vortex(weather)
    vortex_bands = build_vortex_bands(semantic_vortex)

    _write_json(SEMANTIC_VORTEX, semantic_vortex)
    _write_json(VORTEX_BANDS, vortex_bands)

    ts = datetime.now(timezone.utc).isoformat()
    print(f"[v4.0R] Semantic vortex  → {SEMANTIC_VORTEX}")
    print(f"[v4.0R] Vortex bands     → {VORTEX_BANDS}")
    print(f"[v4.0R] Timestamp        → {ts}")


if __name__ == "__main__":
    run_v4_0R_pipeline()
