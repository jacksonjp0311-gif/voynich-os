"""Voynich OS — Semantic Isobar Engine v4.1

Safe, deterministic semantic isobar field for Voynich OS.

Hybrid Inputs (Weather + Vortex)
--------------------------------
  • data/meaning_v3_9/semantic_weather_v3_9.json
       - per-folio weather metrics (continuity, pressure, storm, stability)
  • data/meaning_v3_9/weather_field_v3_9.json
       - ordered folio_ids, stability_index, storm_index, pressure_norm
  • data/meaning_v4_0/semantic_vortex_v4_0.json
       - per-folio vortex / shear metrics (if available)
  • data/meaning_v4_0/vortex_field_v4_0.json
       - ordered folio_ids + vorticity index / magnitude (if available)

Outputs (under data/meaning_v4_1/)
----------------------------------
  • semantic_isobars_v4_1.json
       - per-folio isobar band + metrics (pressure, stability, vorticity)
  • isobar_map_v4_1.json
       - global band statistics + stable / drift zones
  • isobar_field_v4_1.json
       - compact numeric field over folio index (bands + pressure)
  • isobar_legend_v4_1.json
       - legend for isobar structures
  • isobar_ledger_v4_1.jsonl
       - append-only ledger of v4.1 runs

All logic is:
  • Deterministic
  • Non-adaptive
  • Purely analytic (no learning, no randomness)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone


REPO_ROOT = Path(__file__).resolve().parents[1]

MEANING_V39 = REPO_ROOT / "data" / "meaning_v3_9"
MEANING_V40 = REPO_ROOT / "data" / "meaning_v4_0"
OUTDIR      = REPO_ROOT / "data" / "meaning_v4_1"

SEMANTIC_WEATHER = MEANING_V39 / "semantic_weather_v3_9.json"
WEATHER_FIELD    = MEANING_V39 / "weather_field_v3_9.json"

SEMANTIC_VORTEX  = MEANING_V40 / "semantic_vortex_v4_0.json"
VORTEX_FIELD     = MEANING_V40 / "vortex_field_v4_0.json"

SEMANTIC_ISOBARS = OUTDIR / "semantic_isobars_v4_1.json"
ISOBAR_MAP       = OUTDIR / "isobar_map_v4_1.json"
ISOBAR_FIELD     = OUTDIR / "isobar_field_v4_1.json"
ISOBAR_LEGEND    = OUTDIR / "isobar_legend_v4_1.json"
ISOBAR_LEDGER    = OUTDIR / "isobar_ledger_v4_1.jsonl"


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_json_optional(path: Path) -> Any:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def _append_ledger_entry(path: Path, entry: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, sort_keys=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


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
    return max(0.0, min(1.0, (x - lo) / (hi - lo)))


# ────────────────────────────────────────────────────────────────────
# Extraction from v3.9 (Weather) and v4.0 (Vortex)
# ────────────────────────────────────────────────────────────────────

def _build_folio_weather_index(semantic_weather: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    per_folio = semantic_weather.get("per_folio", []) if isinstance(semantic_weather, dict) else []
    return {str(f.get("folio_id")): f for f in per_folio if f.get("folio_id")}


def _build_weather_field_index(weather_field: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    if not isinstance(weather_field, dict):
        return {}
    ids = [str(x) for x in weather_field.get("folio_ids", [])]
    stability = [ _safe_float(v) for v in weather_field.get("stability_index", []) ]
    storm     = [ _safe_float(v) for v in weather_field.get("storm_index", []) ]
    pressure  = [ _safe_float(v) for v in weather_field.get("pressure_norm", []) ]

    out: Dict[str, Dict[str, Any]] = {}
    for i, fid in enumerate(ids):
        out[fid] = {
            "stability_index": stability[i] if i < len(stability) else 0.0,
            "storm_index": storm[i] if i < len(storm) else 0.0,
            "pressure_norm": pressure[i] if i < len(pressure) else 0.0,
        }
    return out


def _build_vortex_index_from_semantic(semantic_vortex: Dict[str, Any]) -> Dict[str, float]:
    """
    Try to read vorticity metrics from semantic_vortex_v4_0.json if available.
    Expects structure similar to semantic_weather: { "per_folio": [...] } with e.g. "vorticity_index".
    """
    out: Dict[str, float] = {}
    if not isinstance(semantic_vortex, dict):
        return out
    per_folio = semantic_vortex.get("per_folio", [])
    for f in per_folio:
        fid = str(f.get("folio_id"))
        if not fid:
            continue
        # prefer explicit vorticity_index, else fall back to generic "vortex_intensity" or "shear_index"
        v = f.get("vorticity_index")
        if v is None:
            v = f.get("vortex_intensity")
        if v is None:
            v = f.get("shear_index")
        out[fid] = _safe_float(v)
    return out


def _build_vortex_index_from_field(vortex_field: Dict[str, Any]) -> Dict[str, float]:
    """
    Fallback: read from vortex_field_v4_0.json if it has
    { "folio_ids": [...], "vorticity_index": [...] } or similar.
    """
    out: Dict[str, float] = {}
    if not isinstance(vortex_field, dict):
        return out

    ids = [str(x) for x in vortex_field.get("folio_ids", [])]
    vlist = vortex_field.get("vorticity_index")
    if vlist is None:
        vlist = vortex_field.get("vortex_intensity")
    if vlist is None:
        vlist = vortex_field.get("shear_index")
    if vlist is None:
        return out

    vvals = [ _safe_float(v) for v in vlist ]
    for i, fid in enumerate(ids):
        out[fid] = vvals[i] if i < len(vvals) else 0.0
    return out


def _build_vortex_index(semantic_vortex: Dict[str, Any], vortex_field: Dict[str, Any]) -> Dict[str, float]:
    """
    Combine semantic_vortex and vortex_field, giving semantic_vortex precedence.
    """
    from_semantic = _build_vortex_index_from_semantic(semantic_vortex)
    from_field = _build_vortex_index_from_field(vortex_field)

    out: Dict[str, float] = {}
    # union of IDs
    all_ids = set(from_semantic.keys()) | set(from_field.keys())
    for fid in all_ids:
        if fid in from_semantic:
            out[fid] = from_semantic[fid]
        else:
            out[fid] = from_field.get(fid, 0.0)
    return out


# ────────────────────────────────────────────────────────────────────
# Isobar builders
# ────────────────────────────────────────────────────────────────────

def _band_pressure(p: float) -> str:
    """
    Deterministic banding of normalized pressure (0..1).
    """
    if p < 0.25:
        return "low"
    if p < 0.50:
        return "mid_low"
    if p < 0.75:
        return "mid_high"
    return "high"


def _band_vorticity(v: float) -> str:
    """
    Deterministic banding for vorticity index.
    """
    av = abs(v)
    if av < 0.10:
        return "calm"
    if av < 0.30:
        return "shear"
    return "vortex"


def _classify_isobar(pressure_band: str, stability: float, storm: float, vort_band: str) -> str:
    """
    Deterministic semantic classification combining pressure band,
    stability, storm index, and vorticity band.
    """
    # Stable plateaus
    if pressure_band in ("mid_high", "high") and stability >= 0.7 and storm <= 0.3 and vort_band != "vortex":
        return "stable_isobar"

    # Shear fronts
    if vort_band == "shear" and storm >= 0.4 and stability <= 0.6:
        return "shear_front"

    # Vortex pockets
    if vort_band == "vortex" and storm >= 0.5:
        return "vortex_pocket"

    # Drift basins
    if pressure_band in ("low", "mid_low") and stability <= 0.4:
        return "drift_basin"

    # Default mixed region
    return "mixed_band"


def build_semantic_isobars(
    semantic_weather: Dict[str, Any],
    weather_field: Dict[str, Any],
    semantic_vortex: Dict[str, Any],
    vortex_field: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build the core semantic isobar structure:
      - per_folio: pressure band, vorticity band, isobar class
    """
    folio_weather = _build_folio_weather_index(semantic_weather)
    wf_index = _build_weather_field_index(weather_field)
    vortex_index = _build_vortex_index(semantic_vortex, vortex_field)

    # derive ranges from weather_field where possible
    # (all normalized already for pressure_norm; we still compute banding)
    per_folio_isobars: List[Dict[str, Any]] = []

    # use union of IDs to be robust
    all_ids = set(folio_weather.keys()) | set(wf_index.keys()) | set(vortex_index.keys())
    ordered_ids = sorted(all_ids)

    for fid in ordered_ids:
        w = folio_weather.get(fid, {})
        wf = wf_index.get(fid, {})

        # base values
        dom_theme = w.get("dominant_theme")
        dom_score = _safe_float(w.get("dominant_score"))
        continuity = _safe_float(w.get("continuity_avg"))
        local_pressure = _safe_float(w.get("local_theme_pressure"))
        local_density = _safe_float(w.get("local_motif_density"))

        stability = _safe_float(wf.get("stability_index", w.get("stability_index", 0.0)))
        storm = _safe_float(wf.get("storm_index", w.get("storm_index", 0.0)))
        pressure_norm = _safe_float(wf.get("pressure_norm"))

        # if weather_field is absent or zero, derive a pseudo-normalized pressure from local_pressure
        if pressure_norm == 0.0 and local_pressure > 0.0:
            # simple monotone transform: p' = p / (1 + p)
            pressure_norm = local_pressure / (1.0 + local_pressure)

        vorticity = vortex_index.get(fid, 0.0)

        pressure_band = _band_pressure(pressure_norm)
        vort_band = _band_vorticity(vorticity)
        isobar_class = _classify_isobar(pressure_band, stability, storm, vort_band)

        per_folio_isobars.append(
            {
                "folio_id": fid,
                "dominant_theme": dom_theme,
                "dominant_score": dom_score,
                "continuity_avg": continuity,
                "local_theme_pressure": local_pressure,
                "local_motif_density": local_density,
                "stability_index": stability,
                "storm_index": storm,
                "pressure_norm": pressure_norm,
                "vorticity_index": vorticity,
                "pressure_band": pressure_band,
                "vorticity_band": vort_band,
                "isobar_class": isobar_class,
            }
        )

    return {
        "meta": {
            "version": "4.1",
            "description": "Semantic isobar metrics across folios (pressure + vorticity bands).",
        },
        "per_folio": per_folio_isobars,
    }


def build_isobar_map(semantic_isobars: Dict[str, Any]) -> Dict[str, Any]:
    """
    Global map of isobar bands, counts, and stable / drift zones.
    """
    per_folio = semantic_isobars.get("per_folio", []) if isinstance(semantic_isobars, dict) else []

    band_counts: Dict[str, int] = {}
    class_counts: Dict[str, int] = {}

    stable_ids: List[str] = []
    drift_ids: List[str] = []
    vortex_ids: List[str] = []

    for f in per_folio:
        band = str(f.get("pressure_band"))
        icls = str(f.get("isobar_class"))
        band_counts[band] = band_counts.get(band, 0) + 1
        class_counts[icls] = class_counts.get(icls, 0) + 1

        fid = str(f.get("folio_id"))
        if icls == "stable_isobar":
            stable_ids.append(fid)
        elif icls == "drift_basin":
            drift_ids.append(fid)
        elif icls == "vortex_pocket":
            vortex_ids.append(fid)

    return {
        "meta": {
            "version": "4.1",
            "description": "Global semantic isobar map (bands, classes, zones).",
        },
        "counts": {
            "pressure_bands": band_counts,
            "isobar_classes": class_counts,
        },
        "zones": {
            "stable_isobars": stable_ids,
            "drift_basins": drift_ids,
            "vortex_pockets": vortex_ids,
        },
    }


def build_isobar_field(semantic_isobars: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compact numeric field snapshot: pressure_norm, vorticity_index, and discrete band codes.
    """
    per_folio = semantic_isobars.get("per_folio", []) if isinstance(semantic_isobars, dict) else []
    if not per_folio:
        return {
            "meta": {
                "version": "4.1",
                "description": "Empty isobar field (no folios).",
            },
            "folio_ids": [],
            "pressure_norm": [],
            "vorticity_index": [],
            "pressure_band_code": [],
            "vorticity_band_code": [],
        }

    folio_ids: List[str] = []
    pressure_norm: List[float] = []
    vorticity_index: List[float] = []
    pressure_band_code: List[int] = []
    vorticity_band_code: List[int] = []

    band_encoding = {
        "low": 0,
        "mid_low": 1,
        "mid_high": 2,
        "high": 3,
    }
    vort_encoding = {
        "calm": 0,
        "shear": 1,
        "vortex": 2,
    }

    for f in per_folio:
        fid = str(f.get("folio_id"))
        folio_ids.append(fid)
        pressure_norm.append(_safe_float(f.get("pressure_norm")))
        vorticity_index.append(_safe_float(f.get("vorticity_index")))
        pb = str(f.get("pressure_band"))
        vb = str(f.get("vorticity_band"))
        pressure_band_code.append(band_encoding.get(pb, -1))
        vorticity_band_code.append(vort_encoding.get(vb, -1))

    return {
        "meta": {
            "version": "4.1",
            "description": "Numeric semantic isobar field over ordered folios.",
        },
        "folio_ids": folio_ids,
        "pressure_norm": pressure_norm,
        "vorticity_index": vorticity_index,
        "pressure_band_code": pressure_band_code,
        "vorticity_band_code": vorticity_band_code,
    }


def build_isobar_legend() -> Dict[str, Any]:
    """
    Human-readable legend for v4.1 isobar structures.
    """
    return {
        "meta": {
            "version": "4.1",
            "description": "Legend for semantic_isobars_v4_1.json and related files.",
        },
        "pressure_bands": {
            "low": "Low semantic pressure: sparse motif density and weak theme pressure.",
            "mid_low": "Moderately low semantic pressure: shallow but present theme anchoring.",
            "mid_high": "Moderately high semantic pressure: strong themes with good continuity.",
            "high": "High semantic pressure: dense thematic / motif fields with strong continuity.",
        },
        "vorticity_bands": {
            "calm": "Low vorticity: smooth semantic flow with minimal shear.",
            "shear": "Intermediate vorticity: thematic shear / turning zones.",
            "vortex": "High vorticity: tightly curved meaning flow (semantic vortices).",
        },
        "isobar_classes": {
            "stable_isobar": "High continuity, high / mid-high pressure, low storm; stable meaning plateaus.",
            "shear_front": "Intermediate vorticity with rising storm; semantic shear fronts.",
            "vortex_pocket": "High vorticity with strong storm; localized semantic vortices.",
            "drift_basin": "Low continuity and low pressure; diffuse, drifting meaning regions.",
            "mixed_band": "Intermediate or mixed conditions not dominated by a single regime.",
        },
        "files": {
            "semantic_isobars_v4_1.json": "Per-folio isobar metrics (bands, classes, indices).",
            "isobar_map_v4_1.json": "Global map of bands, classes, and zones.",
            "isobar_field_v4_1.json": "Numeric field encoding of isobars over folio index.",
            "isobar_legend_v4_1.json": "This explanatory legend.",
        },
    }


# ────────────────────────────────────────────────────────────────────
# Pipeline
# ────────────────────────────────────────────────────────────────────

def run_v4_1_pipeline() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    semantic_weather = _load_json(SEMANTIC_WEATHER)
    weather_field = _load_json(WEATHER_FIELD)
    semantic_vortex = _load_json_optional(SEMANTIC_VORTEX)
    vortex_field = _load_json_optional(VORTEX_FIELD)

    semantic_isobars = build_semantic_isobars(
        semantic_weather=semantic_weather,
        weather_field=weather_field,
        semantic_vortex=semantic_vortex,
        vortex_field=vortex_field,
    )
    isobar_map = build_isobar_map(semantic_isobars)
    isobar_field = build_isobar_field(semantic_isobars)
    isobar_legend = build_isobar_legend()

    _write_json(SEMANTIC_ISOBARS, semantic_isobars)
    _write_json(ISOBAR_MAP, isobar_map)
    _write_json(ISOBAR_FIELD, isobar_field)
    _write_json(ISOBAR_LEGEND, isobar_legend)

    per_folio = semantic_isobars.get("per_folio", [])
    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": ts,
        "version": "4.1",
        "num_folios": len(per_folio),
    }
    _append_ledger_entry(ISOBAR_LEDGER, entry)

    print(f"Semantic isobars  → {SEMANTIC_ISOBARS}")
    print(f"Isobar map        → {ISOBAR_MAP}")
    print(f"Isobar field      → {ISOBAR_FIELD}")
    print(f"Isobar legend     → {ISOBAR_LEGEND}")
    print(f"Ledger append     → {ISOBAR_LEDGER}")


if __name__ == "__main__":
    run_v4_1_pipeline()
