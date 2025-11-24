"""Voynich OS — Meaning-Field Convergence Engine v4.7

Unifies meaning flow, wave, resonance, harmony, and imported payload
into a single meaning-field lattice.

Inputs
------
  • data/meaning_v4_2/semantic_flow_v4_2.json
  • data/meaning_v4_3/meaning_wave_v4_3.json
  • data/meaning_v4_4/semantic_resonance_v4_4.json
  • data/meaning_v4_5/semantic_harmony_v4_5.json
  • import_v4_5/uploaded_payload_v4_5.json (optional, self-healing)

Outputs (under data/meaning_v4_7/)
----------------------------------
  • meaning_field_v4_7.json
       - per-folio unified meaning field metrics
  • field_components_v4_7.json
       - component ranges + global weights
  • field_lattice_v4_7.json
       - ordered lattice + neighbor gradients
  • convergence_summary_v4_7.json
       - global stats + top folios
  • convergence_ledger_v4_7.jsonl
       - append-only run ledger

All logic is deterministic and purely analytic (no learning, no RNG).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone


# ─────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[1]

MEANING_V42 = REPO_ROOT / "data" / "meaning_v4_2"
MEANING_V43 = REPO_ROOT / "data" / "meaning_v4_3"
MEANING_V44 = REPO_ROOT / "data" / "meaning_v4_4"
MEANING_V45 = REPO_ROOT / "data" / "meaning_v4_5"
MEANING_V47 = REPO_ROOT / "data" / "meaning_v4_7"
IMPORT_V45  = REPO_ROOT / "import_v4_5"

FLOW_PATH      = MEANING_V42 / "semantic_flow_v4_2.json"
WAVE_PATH      = MEANING_V43 / "meaning_wave_v4_3.json"
RESONANCE_PATH = MEANING_V44 / "semantic_resonance_v4_4.json"
HARMONY_PATH   = MEANING_V45 / "semantic_harmony_v4_5.json"
IMPORT_PATH    = IMPORT_V45  / "uploaded_payload_v4_5.json"

MEANING_FIELD_PATH   = MEANING_V47 / "meaning_field_v4_7.json"
FIELD_COMPONENTS     = MEANING_V47 / "field_components_v4_7.json"
FIELD_LATTICE        = MEANING_V47 / "field_lattice_v4_7.json"
CONVERGENCE_SUMMARY  = MEANING_V47 / "convergence_summary_v4_7.json"
CONVERGENCE_LEDGER   = MEANING_V47 / "convergence_ledger_v4_7.jsonl"


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _load_json(path: Path, required: bool = True) -> Any:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Required file not found: {path}")
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def _append_ledger(path: Path, entry: Dict[str, Any]) -> None:
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


# ─────────────────────────────────────────────────────────────
# Meaning-field builder
# ─────────────────────────────────────────────────────────────

def build_meaning_field(
    flow_data: Dict[str, Any],
    wave_data: Dict[str, Any],
    res_data: Dict[str, Any],
    harmony_data: Dict[str, Any],
    import_data: Any,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Blend all components into a unified per-folio meaning field."""

    flow_map    = _per_folio_map(flow_data)
    wave_map    = _per_folio_map(wave_data)
    res_map     = _per_folio_map(res_data)
    harmony_map = _per_folio_map(harmony_data)

    import_status = "missing"
    import_map: Dict[str, Dict[str, Any]] = {}

    if isinstance(import_data, dict):
        if import_data.get("status") == "placeholder":
            import_status = "placeholder"
        else:
            # Try to interpret same structure (per_folio list)
            import_map = _per_folio_map(import_data)
            if import_map:
                import_status = "mapped_per_folio"
            if not import_map:
                import_status = "unknown_schema"

    folio_ids = _collect_all_folios(flow_map, wave_map, res_map, harmony_map, import_map)

    records: List[Dict[str, Any]] = []
    continuity_vals: List[float] = []
    harmony_vals: List[float] = []
    vortex_vals: List[float] = []
    external_vals: List[float] = []

    for fid in folio_ids:
        f_flow    = flow_map.get(fid, {})
        f_wave    = wave_map.get(fid, {})
        f_res     = res_map.get(fid, {})
        f_harmony = harmony_map.get(fid, {})
        f_import  = import_map.get(fid, {})

        continuity = _safe_float(
            f_harmony.get("continuity_norm")
            if "continuity_norm" in f_harmony
            else (
                f_flow.get("continuity_avg")
                if "continuity_avg" in f_flow
                else f_res.get("continuity_avg")
            )
        )

        harmony_index = _safe_float(f_harmony.get("harmony_index"))
        vortex_tension = _safe_float(f_harmony.get("vortex_tension"))

        # External component: try multiple reasonable keys in priority order
        external_raw = 0.0
        if isinstance(f_import, dict):
            for key in (
                "external_score",
                "harmony_index",
                "meaning_weight",
                "field_strength",
                "score",
            ):
                if key in f_import:
                    external_raw = _safe_float(f_import.get(key))
                    break

        continuity_vals.append(continuity)
        harmony_vals.append(harmony_index)
        vortex_vals.append(vortex_tension)
        external_vals.append(external_raw)

        records.append(
            {
                "folio_id": fid,
                "continuity_raw": continuity,
                "harmony_raw": harmony_index,
                "vortex_raw": vortex_tension,
                "external_raw": external_raw,
                "dominant_theme": (
                    f_harmony.get("dominant_theme")
                    or f_res.get("dominant_theme")
                    or f_flow.get("dominant_theme")
                    or f_wave.get("dominant_theme")
                ),
            }
        )

    # Global ranges
    cont_min, cont_max = (min(continuity_vals, default=0.0), max(continuity_vals, default=1.0))
    harm_min, harm_max = (min(harmony_vals,   default=0.0), max(harmony_vals,   default=1.0))
    vort_min, vort_max = (min(vortex_vals,    default=0.0), max(vortex_vals,    default=1.0))
    ext_min,  ext_max  = (min(external_vals,  default=0.0), max(external_vals,  default=1.0))

    per_folio: List[Dict[str, Any]] = []
    field_vals: List[float] = []

    for rec in records:
        cont_n = _normalize(rec["continuity_raw"], cont_min, cont_max)
        harm_n = _normalize(rec["harmony_raw"],   harm_min, harm_max)
        vort_n = _normalize(rec["vortex_raw"],    vort_min, vort_max)
        ext_n  = _normalize(rec["external_raw"],  ext_min,  ext_max)

        # Meaning-field strength: harmony + continuity + external hint
        field_strength = (
            0.45 * harm_n +
            0.35 * cont_n +
            0.20 * ext_n
        )

        # Field coherence: high field_strength, low vortex instability
        field_coherence = max(0.0, field_strength * (1.0 - 0.5 * vort_n))

        # Simple regimes
        if field_strength >= 0.8 and field_coherence >= 0.7:
            regime = "high_convergence"
        elif field_strength >= 0.55:
            regime = "moderate_convergence"
        else:
            regime = "low_convergence"

        if vort_n >= 0.6 and field_strength >= 0.5:
            phase = "active_transition"
        elif vort_n <= 0.2 and field_strength >= 0.6:
            phase = "stable_field"
        else:
            phase = "mixed_field"

        item = {
            "folio_id": rec["folio_id"],
            "dominant_theme": rec.get("dominant_theme"),
            "continuity_norm": cont_n,
            "harmony_norm": harm_n,
            "vortex_norm": vort_n,
            "external_norm": ext_n,
            "field_strength": field_strength,
            "field_coherence": field_coherence,
            "field_regime": regime,
            "field_phase": phase,
        }
        per_folio.append(item)
        field_vals.append(field_strength)

    if field_vals:
        f_min = min(field_vals)
        f_max = max(field_vals)
        f_avg = sum(field_vals) / float(len(field_vals))
    else:
        f_min = f_max = f_avg = 0.0

    meaning_field = {
        "meta": {
            "version": "4.7",
            "description": "Unified meaning-field convergence over flow, wave, resonance, harmony, and import payload.",
            "fields": [
                "continuity_norm",
                "harmony_norm",
                "vortex_norm",
                "external_norm",
                "field_strength",
                "field_coherence",
                "field_regime",
                "field_phase",
            ],
            "component_ranges": {
                "continuity": {"min": cont_min, "max": cont_max},
                "harmony":    {"min": harm_min, "max": harm_max},
                "vortex":     {"min": vort_min, "max": vort_max},
                "external":   {"min": ext_min,  "max": ext_max},
            },
            "field_stats": {
                "min": f_min,
                "max": f_max,
                "avg": f_avg,
            },
            "import_status": import_status,
        },
        "per_folio": per_folio,
    }

    components = {
        "meta": {
            "version": "4.7",
            "description": "Component ranges and weights used in meaning-field synthesis.",
        },
        "ranges": {
            "continuity": {"min": cont_min, "max": cont_max},
            "harmony":    {"min": harm_min, "max": harm_max},
            "vortex":     {"min": vort_min, "max": vort_max},
            "external":   {"min": ext_min,  "max": ext_max},
        },
        "weights": {
            "field_strength": {
                "harmony_norm": 0.45,
                "continuity_norm": 0.35,
                "external_norm": 0.20,
            },
            "field_coherence_modulation": {
                "vortex_norm_factor": 0.5
            },
        },
        "import_status": import_status,
    }

    return meaning_field, components


def build_field_lattice(meaning_field: Dict[str, Any]) -> Dict[str, Any]:
    """Construct a simple 1D lattice over folio ordering with neighbor gradients."""
    per_folio = meaning_field.get("per_folio", []) or []
    ordered = sorted(per_folio, key=lambda f: str(f.get("folio_id")))
    n = len(ordered)

    lattice: List[Dict[str, Any]] = []
    for idx, f in enumerate(ordered):
        field_val = _safe_float(f.get("field_strength"))
        prev_val = _safe_float(ordered[idx - 1].get("field_strength")) if idx > 0 else field_val
        next_val = _safe_float(ordered[idx + 1].get("field_strength")) if idx < n - 1 else field_val

        grad_back = field_val - prev_val
        grad_forward = next_val - field_val

        lattice.append(
            {
                "index": idx,
                "folio_id": f.get("folio_id"),
                "field_strength": field_val,
                "field_coherence": _safe_float(f.get("field_coherence")),
                "grad_back": grad_back,
                "grad_forward": grad_forward,
            }
        )

    return {
        "meta": {
            "version": "4.7",
            "description": "Meaning-field lattice over folio ordering with neighbor gradients.",
        },
        "lattice": lattice,
    }


def build_convergence_summary(meaning_field: Dict[str, Any]) -> Dict[str, Any]:
    """Global stats + top folios by field_strength and coherence."""
    per_folio = meaning_field.get("per_folio", []) or []
    meta = meaning_field.get("meta", {}) or {}
    stats = meta.get("field_stats", {}) or {}

    ranked_by_field = sorted(
        per_folio,
        key=lambda f: _safe_float(f.get("field_strength")),
        reverse=True,
    )
    ranked_by_coherence = sorted(
        per_folio,
        key=lambda f: _safe_float(f.get("field_coherence")),
        reverse=True,
    )

    top_field = [
        {
            "folio_id": f.get("folio_id"),
            "field_strength": _safe_float(f.get("field_strength")),
            "field_coherence": _safe_float(f.get("field_coherence")),
            "field_regime": f.get("field_regime"),
            "field_phase": f.get("field_phase"),
        }
        for f in ranked_by_field[:50]
    ]

    top_coherent = [
        {
            "folio_id": f.get("folio_id"),
            "field_strength": _safe_float(f.get("field_strength")),
            "field_coherence": _safe_float(f.get("field_coherence")),
            "field_regime": f.get("field_regime"),
            "field_phase": f.get("field_phase"),
        }
        for f in ranked_by_coherence[:50]
    ]

    regime_counts: Dict[str, int] = {}
    for f in per_folio:
        reg = str(f.get("field_regime") or "unknown")
        regime_counts[reg] = regime_counts.get(reg, 0) + 1

    return {
        "meta": {
            "version": "4.7",
            "description": "Convergence summary over meaning-field lattice.",
        },
        "field_stats": {
            "min": _safe_float(stats.get("min")),
            "max": _safe_float(stats.get("max")),
            "avg": _safe_float(stats.get("avg")),
            "num_folios": len(per_folio),
        },
        "regime_counts": regime_counts,
        "top_field_folios": top_field,
        "top_coherent_folios": top_coherent,
    }


# ─────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────

def run_v4_7_pipeline() -> None:
    MEANING_V47.mkdir(parents=True, exist_ok=True)

    flow_data = _load_json(FLOW_PATH, required=True)
    wave_data = _load_json(WAVE_PATH, required=True)
    res_data  = _load_json(RESONANCE_PATH, required=True)
    harm_data = _load_json(HARMONY_PATH, required=True)
    import_data = _load_json(IMPORT_PATH, required=False)

    meaning_field, components = build_meaning_field(
        flow_data=flow_data,
        wave_data=wave_data,
        res_data=res_data,
        harmony_data=harm_data,
        import_data=import_data,
    )

    lattice = build_field_lattice(meaning_field)
    summary = build_convergence_summary(meaning_field)

    _write_json(MEANING_FIELD_PATH, meaning_field)
    _write_json(FIELD_COMPONENTS,   components)
    _write_json(FIELD_LATTICE,      lattice)
    _write_json(CONVERGENCE_SUMMARY, summary)

    per_folio = meaning_field.get("per_folio", []) or []
    field_stats = meaning_field.get("meta", {}).get("field_stats", {}) or {}
    import_status = meaning_field.get("meta", {}).get("import_status", "unknown")

    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": ts,
        "version": "4.7",
        "num_folios": len(per_folio),
        "field_min": _safe_float(field_stats.get("min")),
        "field_max": _safe_float(field_stats.get("max")),
        "field_avg": _safe_float(field_stats.get("avg")),
        "import_status": import_status,
    }
    _append_ledger(CONVERGENCE_LEDGER, entry)

    print(f"Meaning field      → {MEANING_FIELD_PATH}")
    print(f"Field components   → {FIELD_COMPONENTS}")
    print(f"Field lattice      → {FIELD_LATTICE}")
    print(f"Convergence summary→ {CONVERGENCE_SUMMARY}")
    print(f"Ledger append      → {CONVERGENCE_LEDGER}")


if __name__ == "__main__":
    run_v4_7_pipeline()
