"""Voynich OS — Meaning-Vector Collapse Engine v4.8

Collapses the multi-layer meaning field into per-folio vectors.

Inputs
------
  • data/meaning_v4_2/semantic_flow_v4_2.json
  • data/meaning_v4_3/meaning_wave_v4_3.json
  • data/meaning_v4_4/semantic_resonance_v4_4.json
  • data/meaning_v4_5/semantic_harmony_v4_5.json
  • data/meaning_v4_7/meaning_field_v4_7.json
  • import_v4_5/uploaded_payload_v4_5.json  (optional external hints)

Outputs (under data/meaning_v4_8/)
----------------------------------
  • meaning_vector_v4_8.json
       - per-folio vectors + features
  • vector_clusters_v4_8.json
       - simple regime-based clustering
  • vector_map_v4_8.json
       - folio_id → vector + norms
  • collapse_summary_v4_8.json
       - stats + cluster counts
  • collapse_ledger_v4_8.jsonl
       - append-only run ledger

All logic is:
  • Deterministic
  • Non-adaptive
  • Purely analytic (no learning, no randomness)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[1]

MEANING_V42 = REPO_ROOT / "data" / "meaning_v4_2"
MEANING_V43 = REPO_ROOT / "data" / "meaning_v4_3"
MEANING_V44 = REPO_ROOT / "data" / "meaning_v4_4"
MEANING_V45 = REPO_ROOT / "data" / "meaning_v4_5"
MEANING_V47 = REPO_ROOT / "data" / "meaning_v4_7"
IMPORT_DIR  = REPO_ROOT / "import_v4_5"

OUTDIR = REPO_ROOT / "data" / "meaning_v4_8"

FLOW_PATH      = MEANING_V42 / "semantic_flow_v4_2.json"
WAVE_PATH      = MEANING_V43 / "meaning_wave_v4_3.json"
RESONANCE_PATH = MEANING_V44 / "semantic_resonance_v4_4.json"
HARMONY_PATH   = MEANING_V45 / "semantic_harmony_v4_5.json"
FIELD_PATH     = MEANING_V47 / "meaning_field_v4_7.json"
IMPORT_PATH    = IMPORT_DIR / "uploaded_payload_v4_5.json"

VECTOR_PATH    = OUTDIR / "meaning_vector_v4_8.json"
CLUSTER_PATH   = OUTDIR / "vector_clusters_v4_8.json"
MAP_PATH       = OUTDIR / "vector_map_v4_8.json"
SUMMARY_PATH   = OUTDIR / "collapse_summary_v4_8.json"
LEDGER_PATH    = OUTDIR / "collapse_ledger_v4_8.jsonl"


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _load_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(f"Required file not found: {path}")
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


def _per_folio_map(payload: Any, key: str = "per_folio") -> Dict[str, Dict[str, Any]]:
    if not isinstance(payload, dict):
        return {}
    items = payload.get(key, []) or []
    if not isinstance(items, list):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for entry in items:
        fid = entry.get("folio_id")
        if fid is None:
            continue
        fid_str = str(fid)
        out[fid_str] = entry
    return out


def _collect_ids(*maps: Dict[str, Dict[str, Any]]) -> List[str]:
    ids = set()
    for m in maps:
        ids.update(m.keys())
    return sorted(ids)


# ─────────────────────────────────────────────────────────────
# Core: build meaning vectors
# ─────────────────────────────────────────────────────────────

def build_meaning_vectors(
    flow_data: Dict[str, Any],
    wave_data: Dict[str, Any],
    res_data: Dict[str, Any],
    harmony_data: Dict[str, Any],
    field_data: Dict[str, Any],
    import_payload: Any,
) -> Dict[str, Any]:
    """Build per-folio meaning vectors from all layers."""

    flow_map = _per_folio_map(flow_data)
    wave_map = _per_folio_map(wave_data)
    res_map  = _per_folio_map(res_data)
    harm_map = _per_folio_map(harmony_data)

    # meaning_field_v4_7 from the repair node may be global-only; treat as scalar factor
    field_meta = {}
    if isinstance(field_data, dict):
        field_meta = field_data.get("meta", {}) or field_data

    field_strength_global = _safe_float(field_meta.get("field_strength", 1.0))

    # Optional external hints from uploaded payload
    external_hints: Dict[str, float] = {}
    if isinstance(import_payload, dict):
        # very permissive: look for {"hints": {"folio_id": score, ...}}
        hints = import_payload.get("hints") or import_payload.get("folio_hints")
        if isinstance(hints, dict):
            for k, v in hints.items():
                external_hints[str(k)] = _safe_float(v)

    folio_ids = _collect_ids(flow_map, wave_map, res_map, harm_map)

    vectors: List[Dict[str, Any]] = []
    norms: List[float] = []

    for fid in folio_ids:
        f_flow = flow_map.get(fid, {})
        f_wave = wave_map.get(fid, {})
        f_res  = res_map.get(fid, {})
        f_harm = harm_map.get(fid, {})

        continuity = _safe_float(
            f_flow.get("continuity_avg")
            if "continuity_avg" in f_flow
            else f_res.get("continuity_avg")
        )

        flow_intensity = _safe_float(
            f_flow.get("flow_speed")
            if "flow_speed" in f_flow
            else f_flow.get("transport_index")
        )

        wave_power = _safe_float(
            f_wave.get("wave_amplitude")
            if "wave_amplitude" in f_wave
            else f_wave.get("wave_power")
        )

        resonance_strength = max(
            _safe_float(f_res.get("resonance_index")),
            _safe_float(f_res.get("coherence_index")),
            _safe_float(f_res.get("band_strength")),
        )

        harmony_index = _safe_float(f_harm.get("harmony_index"))
        harmony_band  = f_harm.get("harmony_band")

        field_strength = field_strength_global
        external_hint = external_hints.get(fid, 0.0)

        vector = [
            continuity,
            flow_intensity,
            wave_power,
            resonance_strength,
            harmony_index,
            field_strength,
            external_hint,
        ]

        # simple L2 norm
        norm_sq = sum(x * x for x in vector)
        norm = norm_sq ** 0.5
        norms.append(norm)

        vectors.append(
            {
                "folio_id": fid,
                "vector": vector,
                "features": {
                    "continuity": continuity,
                    "flow_intensity": flow_intensity,
                    "wave_power": wave_power,
                    "resonance_strength": resonance_strength,
                    "harmony_index": harmony_index,
                    "field_strength": field_strength,
                    "external_hint": external_hint,
                    "harmony_band": harmony_band,
                },
                "norm": norm,
            }
        )

    # global stats
    if norms:
        norm_min = min(norms)
        norm_max = max(norms)
        norm_avg = sum(norms) / float(len(norms))
    else:
        norm_min = norm_max = norm_avg = 0.0

    return {
        "meta": {
            "version": "4.8",
            "description": "Per-folio meaning vectors over flow/wave/resonance/harmony/field/external.",
            "vector_dim": 7,
            "norm_stats": {
                "min": norm_min,
                "max": norm_max,
                "avg": norm_avg,
            },
        },
        "per_folio": vectors,
    }


def build_vector_clusters(meaning_vectors: Dict[str, Any]) -> Dict[str, Any]:
    """Simple regime-based clustering over vector norms and harmony index."""

    per_folio = meaning_vectors.get("per_folio", []) or []
    high: List[Dict[str, Any]] = []
    mid: List[Dict[str, Any]] = []
    low: List[Dict[str, Any]] = []

    for rec in per_folio:
        fid = rec.get("folio_id")
        norm = _safe_float(rec.get("norm"))
        feats = rec.get("features", {}) or {}
        h = _safe_float(feats.get("harmony_index"))

        if h >= 0.75 and norm >= 1.0:
            band = "high_coherence_vector"
            high.append(
                {
                    "folio_id": fid,
                    "norm": norm,
                    "harmony_index": h,
                }
            )
        elif h >= 0.5:
            band = "mid_coherence_vector"
            mid.append(
                {
                    "folio_id": fid,
                    "norm": norm,
                    "harmony_index": h,
                }
            )
        else:
            band = "low_coherence_vector"
            low.append(
                {
                    "folio_id": fid,
                    "norm": norm,
                    "harmony_index": h,
                }
            )

        rec["cluster_band"] = band

    return {
        "meta": {
            "version": "4.8",
            "description": "Vector clusters by harmony index + norm.",
        },
        "high_coherence": high,
        "mid_coherence": mid,
        "low_coherence": low,
    }


def build_vector_map(meaning_vectors: Dict[str, Any]) -> Dict[str, Any]:
    """Map folio_id → vector + norm for quick lookup."""
    per_folio = meaning_vectors.get("per_folio", []) or []
    table: Dict[str, Any] = {}
    for rec in per_folio:
        fid = str(rec.get("folio_id"))
        table[fid] = {
            "vector": rec.get("vector"),
            "norm": _safe_float(rec.get("norm")),
            "cluster_band": rec.get("cluster_band"),
        }

    return {
        "meta": {
            "version": "4.8",
            "description": "Folio → meaning vector map.",
        },
        "map": table,
    }


def build_collapse_summary(
    meaning_vectors: Dict[str, Any],
    vector_clusters: Dict[str, Any],
) -> Dict[str, Any]:
    per_folio = meaning_vectors.get("per_folio", []) or []
    n = len(per_folio)
    norm_stats = meaning_vectors.get("meta", {}).get("norm_stats", {}) or {}

    high = vector_clusters.get("high_coherence", []) or []
    mid  = vector_clusters.get("mid_coherence", []) or []
    low  = vector_clusters.get("low_coherence", []) or []

    return {
        "meta": {
            "version": "4.8",
            "description": "Summary of meaning-vector collapse.",
        },
        "counts": {
            "num_folios": n,
            "high_coherence_vectors": len(high),
            "mid_coherence_vectors": len(mid),
            "low_coherence_vectors": len(low),
        },
        "norm_stats": {
            "min": _safe_float(norm_stats.get("min")),
            "max": _safe_float(norm_stats.get("max")),
            "avg": _safe_float(norm_stats.get("avg")),
        },
    }


# ─────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────

def run_v4_8_pipeline() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    flow_data = _load_json(FLOW_PATH, default={"per_folio": []})
    wave_data = _load_json(WAVE_PATH, default={"per_folio": []})
    res_data  = _load_json(RESONANCE_PATH, default={"per_folio": []})
    harm_data = _load_json(HARMONY_PATH, default={"per_folio": []})
    field_data = _load_json(FIELD_PATH, default={})

    import_payload: Any = {}
    if IMPORT_PATH.exists():
        import_payload = _load_json(IMPORT_PATH, default={})

    meaning_vectors = build_meaning_vectors(
        flow_data=flow_data,
        wave_data=wave_data,
        res_data=res_data,
        harmony_data=harm_data,
        field_data=field_data,
        import_payload=import_payload,
    )
    vector_clusters = build_vector_clusters(meaning_vectors)
    vector_map = build_vector_map(meaning_vectors)
    summary = build_collapse_summary(meaning_vectors, vector_clusters)

    _write_json(VECTOR_PATH, meaning_vectors)
    _write_json(CLUSTER_PATH, vector_clusters)
    _write_json(MAP_PATH, vector_map)
    _write_json(SUMMARY_PATH, summary)

    ts = datetime.now(timezone.utc).isoformat()
    ledger_entry = {
        "timestamp": ts,
        "version": "4.8",
        "num_folios": summary.get("counts", {}).get("num_folios", 0),
        "high_coherence_vectors": summary.get("counts", {}).get("high_coherence_vectors", 0),
        "mid_coherence_vectors": summary.get("counts", {}).get("mid_coherence_vectors", 0),
        "low_coherence_vectors": summary.get("counts", {}).get("low_coherence_vectors", 0),
        "norm_min": summary.get("norm_stats", {}).get("min", 0.0),
        "norm_max": summary.get("norm_stats", {}).get("max", 0.0),
        "norm_avg": summary.get("norm_stats", {}).get("avg", 0.0),
    }
    _append_ledger(LEDGER_PATH, ledger_entry)

    print(f"Meaning vectors   → {VECTOR_PATH}")
    print(f"Vector clusters   → {CLUSTER_PATH}")
    print(f"Vector map        → {MAP_PATH}")
    print(f"Collapse summary  → {SUMMARY_PATH}")
    print(f"Ledger append     → {LEDGER_PATH}")


if __name__ == "__main__":
    run_v4_8_pipeline()
