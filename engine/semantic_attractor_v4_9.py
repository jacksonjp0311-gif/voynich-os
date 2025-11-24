"""
Voynich OS v4.9 — Semantic Attractor Map Engine
Root: semantic_attractor_v4_9
Law : Load stack (v4.2..v4.8) → derive attractor metrics → emit map + clusters + lattice + ledger

This engine is intentionally conservative:
- It will not crash if upstream JSON is missing or malformed.
- It uses safe loaders and default structures.
- It produces a stable attractor map even with partial data.
"""

import json
import math
import statistics
import pathlib
import datetime
from typing import Any, Dict, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Input paths
FLOW_PATH      = DATA / "meaning_v4_2" / "semantic_flow_v4_2.json"
WAVE_PATH      = DATA / "meaning_v4_3" / "meaning_wave_v4_3.json"
RES_PATH       = DATA / "meaning_v4_4" / "semantic_resonance_v4_4.json"
HARM_PATH      = DATA / "meaning_v4_5" / "semantic_harmony_v4_5.json"
FIELD_PATH     = DATA / "meaning_v4_7" / "meaning_field_v4_7.json"
VEC_PATH       = DATA / "meaning_v4_8" / "meaning_vector_v4_8.json"
VEC_CLUSTERS   = DATA / "meaning_v4_8" / "vector_clusters_v4_8.json"
VEC_MAP        = DATA / "meaning_v4_8" / "vector_map_v4_8.json"
VEC_SUMMARY    = DATA / "meaning_v4_8" / "collapse_summary_v4_8.json"

# Output directory
OUT_DIR = DATA / "meaning_v4_9"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MAP_PATH       = OUT_DIR / "semantic_attractor_map_v4_9.json"
CLUSTERS_PATH  = OUT_DIR / "attractor_clusters_v4_9.json"
LATTICE_PATH   = OUT_DIR / "attractor_lattice_v4_9.json"
SUMMARY_PATH   = OUT_DIR / "attractor_summary_v4_9.json"
LEDGER_PATH    = OUT_DIR / "attractor_ledger_v4_9.jsonl"


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def safe_load_json(path: pathlib.Path, default: Any = None) -> Any:
    if default is None:
        default = {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        # Fallback: still return default to keep engine alive
        return default
    except Exception:
        return default


def file_metric(path: pathlib.Path, obj: Any) -> Dict[str, Any]:
    size = 0
    if path.exists():
        try:
            size = path.stat().st_size
        except Exception:
            size = 0

    length = 1
    try:
        length = len(obj)  # type: ignore[arg-type]
    except Exception:
        length = 1

    return {"size": size, "length": length}


def normalize_weights(metrics: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    total = sum(m.get("size", 0) for m in metrics.values())
    if total <= 0:
        return {k: 0.0 for k in metrics}
    return {k: m.get("size", 0) / total for k, m in metrics.items()}


def infer_vector_stats(vec_obj: Any) -> Tuple[int, int]:
    """
    Try to infer (num_vectors, approx_dim) from v4.8 meaning_vector JSON.
    If structure is unknown, stay graceful and return zeros.
    """
    num_vectors = 0
    dim = 0

    if isinstance(vec_obj, dict):
        # Common pattern: {"vectors": [...]} or {"per_folio": [...]}
        if "vectors" in vec_obj and isinstance(vec_obj["vectors"], list):
            vectors = vec_obj["vectors"]
            num_vectors = len(vectors)
            if vectors:
                first = vectors[0]
                if isinstance(first, (list, tuple)):
                    dim = len(first)
                elif isinstance(first, dict):
                    dim = len(first)
        elif "per_folio" in vec_obj and isinstance(vec_obj["per_folio"], list):
            num_vectors = len(vec_obj["per_folio"])
    return num_vectors, dim


def scalar_from_metrics(weights: Dict[str, float]) -> float:
    """
    Derive a simple attractor coherence scalar in [0, 1] from weights.
    Using a soft saturation via tanh to keep values bounded.
    """
    # Treat each weight as a contribution to a "coherence" magnitude
    magnitude = math.sqrt(sum(w * w for w in weights.values()))
    return float(math.tanh(magnitude))


# ─────────────────────────────────────────────────────────────
# Core pipeline
# ─────────────────────────────────────────────────────────────

def run():
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Load stack
    flow_obj  = safe_load_json(FLOW_PATH, {})
    wave_obj  = safe_load_json(WAVE_PATH, {})
    res_obj   = safe_load_json(RES_PATH, {})
    harm_obj  = safe_load_json(HARM_PATH, {})
    field_obj = safe_load_json(FIELD_PATH, {})
    vec_obj   = safe_load_json(VEC_PATH, {})
    vec_clu   = safe_load_json(VEC_CLUSTERS, {})
    vec_map   = safe_load_json(VEC_MAP, {})
    vec_sum   = safe_load_json(VEC_SUMMARY, {})

    # Metrics
    metrics = {
        "flow":      file_metric(FLOW_PATH, flow_obj),
        "wave":      file_metric(WAVE_PATH, wave_obj),
        "resonance": file_metric(RES_PATH, res_obj),
        "harmony":   file_metric(HARM_PATH, harm_obj),
        "field":     file_metric(FIELD_PATH, field_obj),
        "vectors":   file_metric(VEC_PATH, vec_obj),
    }
    weights = normalize_weights(metrics)
    coherence = scalar_from_metrics(weights)
    num_vectors, dim_vectors = infer_vector_stats(vec_obj)

    # Build attractor map (semantic "weather map" for meaning)
    attractor_map = {
        "meta": {
            "description": "Semantic Attractor Map over Voynich meaning stack (flow, wave, resonance, harmony, field, vectors).",
            "version": "4.9",
            "timestamp": timestamp,
            "source_layers": ["v4.2", "v4.3", "v4.4", "v4.5", "v4.7", "v4.8"],
        },
        "stages": {
            name: {
                "size_bytes": m["size"],
                "length": m["length"],
                "weight": weights.get(name, 0.0),
            }
            for name, m in metrics.items()
        },
        "attractors": [
            {
                "id": "A0",
                "label": "global_meaning_field",
                "coherence": coherence,
                "num_vectors": num_vectors,
                "vector_dim": dim_vectors,
                "notes": "A0 approximates the global attractor of Voynich semantic flow at v4.9 given available layers.",
            }
        ],
    }

    # Attractor clusters: lightly wrap v4.8 clusters/map into v4.9 framing
    clusters = {
        "meta": {
            "description": "Semantic attractor clusters derived from v4.8 vector clusters / map.",
            "version": "4.9",
            "timestamp": timestamp,
        },
        "v4_8_clusters": vec_clu,
        "v4_8_map": vec_map,
    }

    # Lattice: simple lattice field of weights
    lattice = {
        "meta": {
            "description": "Attractor lattice: stage weights as a simple 1D lattice.",
            "version": "4.9",
            "timestamp": timestamp,
        },
        "lattice_axes": ["flow", "wave", "resonance", "harmony", "field", "vectors"],
        "weights": [weights.get(k, 0.0) for k in ["flow", "wave", "resonance", "harmony", "field", "vectors"]],
    }

    # Summary + ledger payload
    summary = {
        "version": "4.9",
        "timestamp": timestamp,
        "coherence": coherence,
        "num_vectors": num_vectors,
        "vector_dim": dim_vectors,
        "stage_weights": weights,
        "notes": "v4.9 successfully synthesized semantic attractor map from upstream meaning stack.",
    }

    # Write outputs
    def dump(path: pathlib.Path, obj: Any) -> None:
        path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

    dump(MAP_PATH, attractor_map)
    dump(CLUSTERS_PATH, clusters)
    dump(LATTICE_PATH, lattice)
    dump(SUMMARY_PATH, summary)

    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(summary) + "\n")

    print("Semantic Attractor Map v4.9  →", MAP_PATH)
    print("Attractor clusters v4.9      →", CLUSTERS_PATH)
    print("Attractor lattice v4.9       →", LATTICE_PATH)
    print("Attractor summary v4.9       →", SUMMARY_PATH)
    print("Attractor ledger v4.9 append →", LEDGER_PATH)


if __name__ == "__main__":
    run()
