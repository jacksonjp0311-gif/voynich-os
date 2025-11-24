"""Voynich OS — Semantic Harmony Engine v4.5

Meaning-field convergence over flow, wave, and resonance layers.

Inputs
------
  • data/meaning_v4_2/semantic_flow_v4_2.json
      - per-folio semantic flow metrics (continuity, transport, etc.)
  • data/meaning_v4_3/meaning_wave_v4_3.json
      - per-folio wave / lattice metrics
  • data/meaning_v4_4/semantic_resonance_v4_4.json
      - per-folio resonance / coherence bands

Outputs (under data/meaning_v4_5/)
----------------------------------
  • semantic_harmony_v4_5.json
       - per-folio harmony metrics + blended field
  • harmony_index_v4_5.json
       - global harmony index + ranked folios
  • harmony_windows_v4_5.json
       - sliding windows of high-harmony bands
  • harmony_ledger_v4_5.jsonl
       - append-only ledger of v4.5 runs

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

MEANING_V42 = REPO_ROOT / "data" / "meaning_v4_2"
MEANING_V43 = REPO_ROOT / "data" / "meaning_v4_3"
MEANING_V44 = REPO_ROOT / "data" / "meaning_v4_4"
OUTDIR      = REPO_ROOT / "data" / "meaning_v4_5"

FLOW_PATH       = MEANING_V42 / "semantic_flow_v4_2.json"
WAVE_PATH       = MEANING_V43 / "meaning_wave_v4_3.json"
RESONANCE_PATH  = MEANING_V44 / "semantic_resonance_v4_4.json"

SEMANTIC_HARMONY = OUTDIR / "semantic_harmony_v4_5.json"
HARMONY_INDEX    = OUTDIR / "harmony_index_v4_5.json"
HARMONY_WINDOWS  = OUTDIR / "harmony_windows_v4_5.json"
HARMONY_LEDGER   = OUTDIR / "harmony_ledger_v4_5.jsonl"


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
# Extraction helpers
# ────────────────────────────────────────────────────────────────────

def _per_folio_map(payload: Any, key: str = "per_folio") -> Dict[str, Dict[str, Any]]:
    if not isinstance(payload, dict):
        return {}
    items = payload.get(key, [])
    if not isinstance(items, list):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for entry in items:
        fid = str(entry.get("folio_id")) if entry.get("folio_id") is not None else ""
        if not fid:
            continue
        out[fid] = entry
    return out


def _collect_all_folios(*maps: Dict[str, Dict[str, Any]]) -> List[str]:
    ids = set()
    for m in maps:
        ids.update(m.keys())
    return sorted(ids)


# ────────────────────────────────────────────────────────────────────
# Harmony builder
# ────────────────────────────────────────────────────────────────────

def build_semantic_harmony(
    flow_data: Dict[str, Any],
    wave_data: Dict[str, Any],
    resonance_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Blend flow, wave, and resonance into a per-folio harmony index."""
    flow_map = _per_folio_map(flow_data)
    wave_map = _per_folio_map(wave_data)
    res_map  = _per_folio_map(resonance_data)

    folio_ids = _collect_all_folios(flow_map, wave_map, res_map)

    records: List[Dict[str, Any]] = []

    cont_vals: List[float] = []
    res_vals: List[float] = []
    wave_vals: List[float] = []
    flow_vals: List[float] = []

    for fid in folio_ids:
        f_flow = flow_map.get(fid, {})
        f_wave = wave_map.get(fid, {})
        f_res  = res_map.get(fid, {})

        # Continuity as core "stability" proxy
        continuity = _safe_float(
            f_flow.get("continuity_avg")
            if "continuity_avg" in f_flow
            else f_res.get("continuity_avg")
        )

        # Flow speed / transport intensity
        flow_speed = _safe_float(
            f_flow.get("flow_speed")
            if "flow_speed" in f_flow
            else f_flow.get("transport_index")
        )

        # Wave amplitude / power
        wave_amp = _safe_float(
            f_wave.get("wave_amplitude")
            if "wave_amplitude" in f_wave
            else f_wave.get("wave_power")
        )

        # Resonance strength / coherence
        res_strength = max(
            _safe_float(f_res.get("resonance_index")),
            _safe_float(f_res.get("coherence_index")),
            _safe_float(f_res.get("band_strength")),
        )

        cont_vals.append(continuity)
        res_vals.append(res_strength)
        wave_vals.append(wave_amp)
        flow_vals.append(flow_speed)

        records.append(
            {
                "folio_id": fid,
                "continuity_raw": continuity,
                "flow_speed_raw": flow_speed,
                "wave_amplitude_raw": wave_amp,
                "resonance_raw": res_strength,
                "dominant_theme": f_res.get("dominant_theme")
                    or f_flow.get("dominant_theme")
                    or f_wave.get("dominant_theme"),
            }
        )

    # Global ranges
    cont_min, cont_max = (min(cont_vals, default=0.0), max(cont_vals, default=1.0))
    res_min,  res_max  = (min(res_vals,  default=0.0), max(res_vals,  default=1.0))
    wav_min,  wav_max  = (min(wave_vals, default=0.0), max(wave_vals, default=1.0))
    flow_min, flow_max = (min(flow_vals, default=0.0), max(flow_vals, default=1.0))

    # Second pass: normalize + compute harmony metrics
    per_folio: List[Dict[str, Any]] = []
    harmony_values: List[float] = []

    for rec in records:
        cont_norm = _normalize(rec["continuity_raw"], cont_min, cont_max)
        res_norm  = _normalize(rec["resonance_raw"],  res_min,  res_max)
        wav_norm  = _normalize(rec["wave_amplitude_raw"], wav_min, wav_max)
        flow_norm = _normalize(rec["flow_speed_raw"],  flow_min, flow_max)

        # Harmony index: continuity + resonance + wave blend
        harmony_index = (
            0.4 * cont_norm
            + 0.4 * res_norm
            + 0.2 * wav_norm
        )

        # Vortex tension: high flow, lower continuity
        vortex_tension = max(0.0, flow_norm * (1.0 - cont_norm))

        # Classification
        if harmony_index >= 0.8:
            band = "high_harmony_band"
        elif harmony_index >= 0.55:
            band = "moderate_harmony_band"
        else:
            band = "low_harmony_band"

        if vortex_tension >= 0.6 and harmony_index >= 0.5:
            phase = "transitional_wavefront"
        elif vortex_tension <= 0.2 and harmony_index >= 0.6:
            phase = "stable_convergence"
        else:
            phase = "mixed_phase"

        item = {
            "folio_id": rec["folio_id"],
            "dominant_theme": rec.get("dominant_theme"),
            "continuity_norm": cont_norm,
            "resonance_norm": res_norm,
            "wave_norm": wav_norm,
            "flow_norm": flow_norm,
            "harmony_index": harmony_index,
            "vortex_tension": vortex_tension,
            "harmony_band": band,
            "phase_state": phase,
        }
        per_folio.append(item)
        harmony_values.append(harmony_index)

    # Simple global stats
    if harmony_values:
        h_min = min(harmony_values)
        h_max = max(harmony_values)
        h_avg = sum(harmony_values) / float(len(harmony_values))
    else:
        h_min = h_max = h_avg = 0.0

    return {
        "meta": {
            "version": "4.5",
            "description": "Semantic harmony over meaning flow, wave, and resonance.",
            "fields": [
                "continuity_norm",
                "resonance_norm",
                "wave_norm",
                "flow_norm",
                "harmony_index",
                "vortex_tension",
                "harmony_band",
                "phase_state",
            ],
            "harmony_stats": {
                "min": h_min,
                "max": h_max,
                "avg": h_avg,
            },
        },
        "per_folio": per_folio,
    }


def build_harmony_index(semantic_harmony: Dict[str, Any]) -> Dict[str, Any]:
    """Global harmony index + ranked folios."""
    per_folio = semantic_harmony.get("per_folio", []) or []

    ranked = sorted(
        per_folio,
        key=lambda f: _safe_float(f.get("harmony_index")),
        reverse=True,
    )

    top_harmony = [
        {
            "folio_id": f.get("folio_id"),
            "harmony_index": _safe_float(f.get("harmony_index")),
            "vortex_tension": _safe_float(f.get("vortex_tension")),
            "harmony_band": f.get("harmony_band"),
            "phase_state": f.get("phase_state"),
        }
        for f in ranked[:50]
    ]

    # Also rank by vortex_tension (interesting transition regions)
    vortex_ranked = sorted(
        per_folio,
        key=lambda f: _safe_float(f.get("vortex_tension")),
        reverse=True,
    )

    top_vortex = [
        {
            "folio_id": f.get("folio_id"),
            "harmony_index": _safe_float(f.get("harmony_index")),
            "vortex_tension": _safe_float(f.get("vortex_tension")),
            "harmony_band": f.get("harmony_band"),
            "phase_state": f.get("phase_state"),
        }
        for f in vortex_ranked[:50]
    ]

    return {
        "meta": {
            "version": "4.5",
            "description": "Harmony index and ranked folio lists.",
        },
        "top_harmony_folios": top_harmony,
        "top_vortex_folios": top_vortex,
    }


def build_harmony_windows(semantic_harmony: Dict[str, Any], window_size: int = 5) -> Dict[str, Any]:
    """Sliding windows over folio ordering to find convergence zones."""
    per_folio = semantic_harmony.get("per_folio", []) or []
    if not per_folio:
        return {
            "meta": {
                "version": "4.5",
                "description": "Empty harmony windows (no folios).",
            },
            "windows": [],
        }

    # Order by folio_id lexicographically
    ordered = sorted(per_folio, key=lambda f: str(f.get("folio_id")))
    n = len(ordered)
    ws = max(1, int(window_size))

    windows: List[Dict[str, Any]] = []
    for i in range(0, n - ws + 1):
        chunk = ordered[i : i + ws]
        ids = [str(f.get("folio_id")) for f in chunk]
        vals = [_safe_float(f.get("harmony_index")) for f in chunk]

        if vals:
            avg_h = sum(vals) / float(len(vals))
            min_h = min(vals)
            max_h = max(vals)
        else:
            avg_h = min_h = max_h = 0.0

        # Simple classification of window regime
        if avg_h >= 0.75:
            reg = "strong_convergence_window"
        elif avg_h >= 0.55:
            reg = "moderate_convergence_window"
        else:
            reg = "low_convergence_window"

        windows.append(
            {
                "start_folio": ids[0],
                "end_folio": ids[-1],
                "folio_ids": ids,
                "avg_harmony": avg_h,
                "min_harmony": min_h,
                "max_harmony": max_h,
                "regime": reg,
            }
        )

    return {
        "meta": {
            "version": "4.5",
            "description": "Sliding harmony windows over folio ordering.",
            "window_size": ws,
        },
        "windows": windows,
    }


# ────────────────────────────────────────────────────────────────────
# Pipeline
# ────────────────────────────────────────────────────────────────────

def run_v4_5_pipeline() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    flow_data = _load_json(FLOW_PATH)
    wave_data = _load_json(WAVE_PATH)
    resonance_data = _load_json(RESONANCE_PATH)

    semantic_harmony = build_semantic_harmony(
        flow_data=flow_data,
        wave_data=wave_data,
        resonance_data=resonance_data,
    )
    harmony_index = build_harmony_index(semantic_harmony)
    harmony_windows = build_harmony_windows(semantic_harmony, window_size=5)

    _write_json(SEMANTIC_HARMONY, semantic_harmony)
    _write_json(HARMONY_INDEX, harmony_index)
    _write_json(HARMONY_WINDOWS, harmony_windows)

    per_folio = semantic_harmony.get("per_folio", []) or []
    h_stats = semantic_harmony.get("meta", {}).get("harmony_stats", {})

    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": ts,
        "version": "4.5",
        "num_folios": len(per_folio),
        "harmony_min": _safe_float(h_stats.get("min")),
        "harmony_max": _safe_float(h_stats.get("max")),
        "harmony_avg": _safe_float(h_stats.get("avg")),
    }
    _append_ledger_entry(HARMONY_LEDGER, entry)

    print(f"Semantic harmony  → {SEMANTIC_HARMONY}")
    print(f"Harmony index     → {HARMONY_INDEX}")
    print(f"Harmony windows   → {HARMONY_WINDOWS}")
    print(f"Ledger append     → {HARMONY_LEDGER}")


if __name__ == "__main__":
    run_v4_5_pipeline()
