"""Voynich OS — Semantic Resonance Engine v4.4

Safe, deterministic semantic resonance field for Voynich OS.

Inputs
------
  • data/meaning_v3_8/semantic_horizon_v3_8.json
      - per-folio continuity + pressure + motif density
  • data/meaning_v3_9/semantic_weather_v3_9.json
      - per-folio stability / storm / drift / pressure trend
  • data/meaning_v4_0/semantic_vortex_v4_0.json
      - per-folio vortex / shear metrics            (if present)
  • data/meaning_v4_1/semantic_isobar_v4_1.json
      - per-folio pressure band metrics             (if present)
  • data/meaning_v4_2/semantic_flow_v4_2.json
      - per-folio flow magnitude / curvature        (if present)
  • data/meaning_v4_3/meaning_wave_v4_3.json
      - per-folio wave amplitude / spectrum index   (if present)

Outputs (under data/meaning_v4_4/)
----------------------------------
  • semantic_resonance_v4_4.json
       - per-folio resonance metrics
  • resonance_field_v4_4.json
       - numeric resonance field over ordered folios
  • resonance_bands_v4_4.json
       - contiguous high-resonance bands
  • resonance_summary_v4_4.json
       - top resonance nodes + global stats
  • resonance_ledger_v4_4.jsonl
       - append-only ledger of v4.4 runs

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

MEANING_V38 = REPO_ROOT / "data" / "meaning_v3_8"
MEANING_V39 = REPO_ROOT / "data" / "meaning_v3_9"
MEANING_V40 = REPO_ROOT / "data" / "meaning_v4_0"
MEANING_V41 = REPO_ROOT / "data" / "meaning_v4_1"
MEANING_V42 = REPO_ROOT / "data" / "meaning_v4_2"
MEANING_V43 = REPO_ROOT / "data" / "meaning_v4_3"
OUTDIR      = REPO_ROOT / "data" / "meaning_v4_4"

SEMANTIC_HORIZON = MEANING_V38 / "semantic_horizon_v3_8.json"
SEMANTIC_WEATHER = MEANING_V39 / "semantic_weather_v3_9.json"
SEMANTIC_VORTEX  = MEANING_V40 / "semantic_vortex_v4_0.json"
SEMANTIC_ISOBAR  = MEANING_V41 / "semantic_isobar_v4_1.json"
SEMANTIC_FLOW    = MEANING_V42 / "semantic_flow_v4_2.json"
MEANING_WAVE     = MEANING_V43 / "meaning_wave_v4_3.json"

SEMANTIC_RESONANCE = OUTDIR / "semantic_resonance_v4_4.json"
RESONANCE_FIELD    = OUTDIR / "resonance_field_v4_4.json"
RESONANCE_BANDS    = OUTDIR / "resonance_bands_v4_4.json"
RESONANCE_SUMMARY  = OUTDIR / "resonance_summary_v4_4.json"
RESONANCE_LEDGER   = OUTDIR / "resonance_ledger_v4_4.jsonl"


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
    v = (x - lo) / (hi - lo)
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


# ────────────────────────────────────────────────────────────────────
# Extraction helpers
# ────────────────────────────────────────────────────────────────────

def _build_folio_map_from_per_folio(obj: Any, key: str = "per_folio") -> Dict[str, Dict[str, Any]]:
    if not isinstance(obj, dict):
        return {}
    arr = obj.get(key) or []
    out: Dict[str, Dict[str, Any]] = {}
    for entry in arr:
        fid = str(entry.get("folio_id") or "")
        if not fid:
            continue
        out[fid] = entry
    return out


def _collect_all_folio_ids(*maps: Dict[str, Dict[str, Any]]) -> List[str]:
    ids = set()
    for m in maps:
        ids.update(m.keys())
    return sorted(ids)


def _global_range_from_field(
    folio_map: Dict[str, Dict[str, Any]],
    field: str,
    default: Tuple[float, float, float] = (0.0, 0.0, 1.0),
) -> Tuple[float, float, float]:
    vals = [_safe_float(v.get(field)) for v in folio_map.values()]
    if not vals:
        return default
    mn = min(vals)
    mx = max(vals)
    av = sum(vals) / float(len(vals))
    return (mn, av, mx)


# ────────────────────────────────────────────────────────────────────
# Resonance builders
# ────────────────────────────────────────────────────────────────────

def build_semantic_resonance(
    semantic_horizon: Dict[str, Any],
    semantic_weather: Dict[str, Any],
    semantic_vortex: Dict[str, Any],
    semantic_isobar: Dict[str, Any],
    semantic_flow: Dict[str, Any],
    meaning_wave: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build the core semantic resonance structure:
      - per-folio resonance metrics
    """
    horizon_map = _build_folio_map_from_per_folio(semantic_horizon, "per_folio")
    weather_map = _build_folio_map_from_per_folio(semantic_weather, "per_folio")
    vortex_map  = _build_folio_map_from_per_folio(semantic_vortex, "per_folio")
    isobar_map  = _build_folio_map_from_per_folio(semantic_isobar, "per_folio")
    flow_map    = _build_folio_map_from_per_folio(semantic_flow, "per_folio")
    wave_map    = _build_folio_map_from_per_folio(meaning_wave, "per_folio")

    folio_ids = _collect_all_folio_ids(
        horizon_map, weather_map, vortex_map, isobar_map, flow_map, wave_map
    )

    # Build approximate global ranges for normalization
    cont_min, cont_avg, cont_max = _global_range_from_field(horizon_map, "continuity_avg", (0.0, 0.0, 1.0))
    press_min, press_avg, press_max = _global_range_from_field(horizon_map, "local_theme_pressure", (0.0, 0.0, 1.0))
    dens_min, dens_avg, dens_max = _global_range_from_field(horizon_map, "local_motif_density", (0.0, 0.0, 1.0))

    per_folio_resonance: List[Dict[str, Any]] = []

    for fid in folio_ids:
        h = horizon_map.get(fid, {})
        w = weather_map.get(fid, {})
        v = vortex_map.get(fid, {})
        b = isobar_map.get(fid, {})
        fl = flow_map.get(fid, {})
        wa = wave_map.get(fid, {})

        # Base horizon / weather
        continuity = _safe_float(h.get("continuity_avg"))
        continuity_norm = _normalize(continuity, cont_min, cont_max)

        local_pressure = _safe_float(h.get("local_theme_pressure"))
        pressure_norm_h = _normalize(local_pressure, press_min, press_max)

        motif_density = _safe_float(h.get("local_motif_density"))
        motif_norm = _normalize(motif_density, dens_min, dens_max)

        stability = _safe_float(w.get("stability_index"))
        storm = _safe_float(w.get("storm_index"))
        drift = _safe_float(w.get("drift_index"))
        pressure_trend = w.get("pressure_trend") or "steady"
        weather_category = w.get("category") or "unknown"

        # Vortex / isobar / flow / wave contributions (all treated as [0,1]-ish, clamped)
        vortex_strength = _safe_float(
            v.get("vortex_strength") or v.get("vortex_index") or v.get("swirl_index")
        )
        if vortex_strength < 0.0:
            vortex_strength = 0.0

        isobar_pressure = _safe_float(
            b.get("pressure_norm") or b.get("isobar_pressure") or b.get("band_pressure")
        )
        if isobar_pressure < 0.0:
            isobar_pressure = 0.0

        flow_magnitude = _safe_float(
            fl.get("flow_intensity") or fl.get("flow_magnitude") or fl.get("transport_index")
        )
        if flow_magnitude < 0.0:
            flow_magnitude = 0.0

        wave_amplitude = _safe_float(
            wa.get("wave_amplitude") or wa.get("amplitude_index") or wa.get("wave_power")
        )
        if wave_amplitude < 0.0:
            wave_amplitude = 0.0

        # Base coherence from continuity + stability vs storm
        base_coherence = (continuity_norm + stability + (1.0 - min(storm, 1.0))) / 3.0

        # Energy-like contribution from pressure + vortex + flow + wave
        energy_terms = [pressure_norm_h, isobar_pressure, vortex_strength, flow_magnitude, wave_amplitude]
        energy_sum = sum(energy_terms)
        energy = energy_sum / float(len(energy_terms)) if energy_terms else 0.0

        # Simple shear index from storm + vortex + flow
        shear_index = min(
            1.0,
            (storm + vortex_strength + flow_magnitude) / 3.0
        )

        # Resonance index as balanced combination
        resonance_index = 0.5 * base_coherence + 0.5 * energy
        if resonance_index < 0.0:
            resonance_index = 0.0
        if resonance_index > 1.0:
            resonance_index = 1.0

        # Approximate coherence_index in Codex spirit: high continuity + moderate energy, low drift
        coherence_index = max(
            0.0,
            min(
                1.0,
                0.5 * continuity_norm + 0.3 * energy + 0.2 * (1.0 - min(drift, 1.0)),
            ),
        )

        # Category assignment (deterministic)
        if resonance_index >= 0.7 and coherence_index >= 0.6:
            band = "high_resonance_band"
        elif resonance_index <= 0.3 and base_coherence <= 0.3:
            band = "low_resonance_gap"
        elif shear_index >= 0.6 and resonance_index >= 0.4:
            band = "interference_node"
        else:
            band = "transitional_zone"

        # Anchor flag: very high coherence but low volatility / storm
        is_anchor = (coherence_index >= 0.75 and storm <= 0.3)

        per_folio_resonance.append(
            {
                "folio_id": fid,
                "dominant_theme": h.get("dominant_theme") or w.get("dominant_theme"),
                "continuity_avg": continuity,
                "continuity_norm": continuity_norm,
                "stability_index": stability,
                "storm_index": storm,
                "drift_index": drift,
                "local_theme_pressure": local_pressure,
                "pressure_norm_horizon": pressure_norm_h,
                "motif_density": motif_density,
                "motif_norm": motif_norm,
                "vortex_strength": vortex_strength,
                "isobar_pressure": isobar_pressure,
                "flow_magnitude": flow_magnitude,
                "wave_amplitude": wave_amplitude,
                "base_coherence": base_coherence,
                "energy_index": energy,
                "shear_index": shear_index,
                "resonance_index": resonance_index,
                "coherence_index": coherence_index,
                "resonance_band": band,
                "pressure_trend": pressure_trend,
                "weather_category": weather_category,
                "is_anchor_node": is_anchor,
            }
        )

    return {
        "meta": {
            "version": "4.4",
            "description": "Semantic resonance metrics across folios.",
        },
        "per_folio": per_folio_resonance,
    }


def build_resonance_field(semantic_resonance: Dict[str, Any]) -> Dict[str, Any]:
    per_folio = semantic_resonance.get("per_folio", [])
    if not per_folio:
        return {
            "meta": {
                "version": "4.4",
                "description": "Empty resonance field (no folios).",
            },
            "folio_ids": [],
            "resonance_index": [],
            "coherence_index": [],
            "shear_index": [],
        }

    # Deterministic ordering by folio_id
    per_folio_sorted = sorted(per_folio, key=lambda f: str(f.get("folio_id")))
    folio_ids = [f.get("folio_id") for f in per_folio_sorted]
    resonance_vals = [_safe_float(f.get("resonance_index")) for f in per_folio_sorted]
    coherence_vals = [_safe_float(f.get("coherence_index")) for f in per_folio_sorted]
    shear_vals = [_safe_float(f.get("shear_index")) for f in per_folio_sorted]

    return {
        "meta": {
            "version": "4.4",
            "description": "Numeric semantic resonance field over ordered folios.",
        },
        "folio_ids": folio_ids,
        "resonance_index": resonance_vals,
        "coherence_index": coherence_vals,
        "shear_index": shear_vals,
    }


def build_resonance_bands(semantic_resonance: Dict[str, Any]) -> Dict[str, Any]:
    per_folio = semantic_resonance.get("per_folio", [])
    if not per_folio:
        return {
            "meta": {
                "version": "4.4",
                "description": "Empty resonance bands (no folios).",
            },
            "high_bands": [],
            "low_gaps": [],
            "interference_nodes": [],
        }

    per_folio_sorted = sorted(per_folio, key=lambda f: str(f.get("folio_id")))

    # Helper to extract contiguous bands above/below a threshold
    def extract_bands(threshold: float, mode: str) -> List[Dict[str, Any]]:
        bands: List[Dict[str, Any]] = []
        current: List[Dict[str, Any]] = []

        for f in per_folio_sorted:
            r = _safe_float(f.get("resonance_index"))
            cond = (r >= threshold) if mode == "high" else (r <= threshold)
            if cond:
                current.append(f)
            else:
                if current:
                    bands.append(
                        {
                            "start_folio": current[0].get("folio_id"),
                            "end_folio": current[-1].get("folio_id"),
                            "size": len(current),
                            "avg_resonance": sum(
                                _safe_float(x.get("resonance_index")) for x in current
                            )
                            / float(len(current)),
                        }
                    )
                    current = []
        if current:
            bands.append(
                {
                    "start_folio": current[0].get("folio_id"),
                    "end_folio": current[-1].get("folio_id"),
                    "size": len(current),
                    "avg_resonance": sum(
                        _safe_float(x.get("resonance_index")) for x in current
                    )
                    / float(len(current)),
                }
            )
        return bands

    high_bands = extract_bands(0.65, mode="high")
    low_gaps = extract_bands(0.30, mode="low")

    interference_nodes = [
        {
            "folio_id": f.get("folio_id"),
            "resonance_index": _safe_float(f.get("resonance_index")),
            "shear_index": _safe_float(f.get("shear_index")),
        }
        for f in per_folio_sorted
        if f.get("resonance_band") == "interference_node"
    ]

    return {
        "meta": {
            "version": "4.4",
            "description": "Resonance bands and interference nodes.",
        },
        "high_bands": high_bands,
        "low_gaps": low_gaps,
        "interference_nodes": interference_nodes,
    }


def build_resonance_summary(semantic_resonance: Dict[str, Any]) -> Dict[str, Any]:
    per_folio = semantic_resonance.get("per_folio", [])
    if not per_folio:
        return {
            "meta": {
                "version": "4.4",
                "description": "Empty resonance summary (no folios).",
            },
            "global_stats": {},
            "top_resonant_folios": [],
            "anchor_nodes": [],
        }

    vals = [_safe_float(f.get("resonance_index")) for f in per_folio]
    coh_vals = [_safe_float(f.get("coherence_index")) for f in per_folio]

    global_stats = {
        "resonance_min": min(vals),
        "resonance_max": max(vals),
        "resonance_avg": sum(vals) / float(len(vals)),
        "coherence_min": min(coh_vals),
        "coherence_max": max(coh_vals),
        "coherence_avg": sum(coh_vals) / float(len(coh_vals)),
        "num_folios": len(per_folio),
    }

    top_res = sorted(
        per_folio,
        key=lambda f: _safe_float(f.get("resonance_index")),
        reverse=True,
    )[:25]

    anchor_nodes = [
        {
            "folio_id": f.get("folio_id"),
            "resonance_index": _safe_float(f.get("resonance_index")),
            "coherence_index": _safe_float(f.get("coherence_index")),
        }
        for f in per_folio
        if bool(f.get("is_anchor_node"))
    ]

    return {
        "meta": {
            "version": "4.4",
            "description": "Resonance summary, including top folios and anchor nodes.",
        },
        "global_stats": global_stats,
        "top_resonant_folios": [
            {
                "folio_id": f.get("folio_id"),
                "resonance_index": _safe_float(f.get("resonance_index")),
                "coherence_index": _safe_float(f.get("coherence_index")),
                "resonance_band": f.get("resonance_band"),
            }
            for f in top_res
        ],
        "anchor_nodes": anchor_nodes,
    }


# ────────────────────────────────────────────────────────────────────
# Pipeline
# ────────────────────────────────────────────────────────────────────

def run_v4_4_pipeline() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    semantic_horizon = _load_json(SEMANTIC_HORIZON)
    semantic_weather = _load_json(SEMANTIC_WEATHER)
    semantic_vortex = _load_json_optional(SEMANTIC_VORTEX)
    semantic_isobar = _load_json_optional(SEMANTIC_ISOBAR)
    semantic_flow = _load_json_optional(SEMANTIC_FLOW)
    meaning_wave = _load_json_optional(MEANING_WAVE)

    semantic_resonance = build_semantic_resonance(
        semantic_horizon=semantic_horizon,
        semantic_weather=semantic_weather,
        semantic_vortex=semantic_vortex,
        semantic_isobar=semantic_isobar,
        semantic_flow=semantic_flow,
        meaning_wave=meaning_wave,
    )
    resonance_field = build_resonance_field(semantic_resonance)
    resonance_bands = build_resonance_bands(semantic_resonance)
    resonance_summary = build_resonance_summary(semantic_resonance)

    _write_json(SEMANTIC_RESONANCE, semantic_resonance)
    _write_json(RESONANCE_FIELD, resonance_field)
    _write_json(RESONANCE_BANDS, resonance_bands)
    _write_json(RESONANCE_SUMMARY, resonance_summary)

    # Ledger entry
    ts = datetime.now(timezone.utc).isoformat()
    per_folio = semantic_resonance.get("per_folio", [])
    entry = {
        "timestamp": ts,
        "version": "4.4",
        "num_folios": len(per_folio),
    }
    _append_ledger_entry(RESONANCE_LEDGER, entry)

    print(f"Semantic resonance → {SEMANTIC_RESONANCE}")
    print(f"Resonance field    → {RESONANCE_FIELD}")
    print(f"Resonance bands    → {RESONANCE_BANDS}")
    print(f"Resonance summary  → {RESONANCE_SUMMARY}")
    print(f"Ledger append      → {RESONANCE_LEDGER}")


if __name__ == "__main__":
    run_v4_4_pipeline()
