"""
Voynich OS — Folio Cluster Engine v3.2

Loads per-folio vectors from data/meaning_v3_2/page_vectors_index.json
and performs a simple, deterministic k-means-style clustering.

Outputs:
    data/meaning_v3_2/clusters/cluster_summary_v3_2.json
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MEANING_ROOT = REPO_ROOT / "data" / "meaning_v3_2"
INDEX_PATH = MEANING_ROOT / "page_vectors_index.json"
CLUSTER_DIR = MEANING_ROOT / "clusters"
SUMMARY_PATH = CLUSTER_DIR / "cluster_summary_v3_2.json"


def _load_index() -> Dict[str, Any]:
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"Missing index: {INDEX_PATH}")
    text = INDEX_PATH.read_text(encoding="utf-8")
    return json.loads(text)


def _build_dimension_lists(index: Dict[str, Any]):
    rel_keys = set()
    state_keys = set()

    for folio, data in index.items():
        for r in data.get("rel_freq", {}).keys():
            rel_keys.add(r)
        for s in data.get("state_freq", {}).keys():
            state_keys.add(s)

    rel_list = sorted(rel_keys)
    state_list = sorted(state_keys)
    return rel_list, state_list


def _vector_for_folio(data: Dict[str, Any],
                      rel_list: List[str],
                      state_list: List[str]) -> List[float]:
    total_tokens = float(data.get("total_tokens", 0) or 0)
    total_lines = float(data.get("total_lines", 0) or 0)
    rel_freq = data.get("rel_freq", {})
    state_freq = data.get("state_freq", {})

    tokens_norm = 0.0
    lines_norm = 0.0

    if total_tokens > 0:
        tokens_norm = min(total_tokens / 1000.0, 1.0)
    if total_lines > 0:
        lines_norm = min(total_lines / 200.0, 1.0)

    vec: List[float] = [tokens_norm, lines_norm]

    for r in rel_list:
        vec.append(float(rel_freq.get(r, 0.0)))
    for s in state_list:
        vec.append(float(state_freq.get(s, 0.0)))

    return vec


def _l2_distance(a: List[float], b: List[float]) -> float:
    # Basic Euclidean distance, deterministic.
    total = 0.0
    for x, y in zip(a, b):
        diff = x - y
        total += diff * diff
    return total ** 0.5


def _mean_vector(vectors: List[List[float]]) -> List[float]:
    if not vectors:
        return []
    n = len(vectors)
    dim = len(vectors[0])
    sums = [0.0] * dim
    for v in vectors:
        for i, val in enumerate(v):
            sums[i] += val
    return [s / float(n) for s in sums]


def cluster_folios(k: int = 6) -> Dict[str, Any]:
    CLUSTER_DIR.mkdir(parents=True, exist_ok=True)

    index = _load_index()
    folios = sorted(index.keys())

    if not folios:
        raise RuntimeError("No folios found in index; run page_vectorizer first.")

    rel_list, state_list = _build_dimension_lists(index)

    vectors: Dict[str, List[float]] = {}
    for folio in folios:
        v = _vector_for_folio(index[folio], rel_list, state_list)
        vectors[folio] = v

    if len(folios) < k:
        k = len(folios)

    if k <= 0:
        raise RuntimeError("Cannot cluster with k <= 0.")

    # Deterministic k-means: first k folios as initial centroids
    centroids: List[List[float]] = []
    for folio in folios[:k]:
        centroids.append(vectors[folio])

    assignments: Dict[str, int] = {}
    max_iter = 20

    for _ in range(max_iter):
        changed = False

        # Assignment step
        for folio in folios:
            v = vectors[folio]
            best_idx = 0
            best_dist = _l2_distance(v, centroids[0])

            for ci in range(1, k):
                d = _l2_distance(v, centroids[ci])
                if d < best_dist:
                    best_dist = d
                    best_idx = ci

            old = assignments.get(folio, None)
            if old != best_idx:
                assignments[folio] = best_idx
                changed = True

        # If nothing changed, we are stable
        if not changed:
            break

        # Update step
        new_centroids: List[List[float]] = []
        for ci in range(k):
            bucket = [vectors[f] for f, a in assignments.items() if a == ci]
            if bucket:
                new_centroids.append(_mean_vector(bucket))
            else:
                # If a cluster is empty, keep its old centroid
                new_centroids.append(centroids[ci])
        centroids = new_centroids

    # Build summary structure
    clusters: List[Dict[str, Any]] = []
    for ci in range(k):
        members = [f for f, a in assignments.items() if a == ci]
        clusters.append(
            {
                "cluster_id": ci,
                "size": len(members),
                "members": members,
            }
        )

    summary: Dict[str, Any] = {
        "k": k,
        "dimensions": ["tokens_norm", "lines_norm"]
        + [f"rel:{r}" for r in rel_list]
        + [f"state:{s}" for s in state_list],
        "clusters": clusters,
        "index_path": str(INDEX_PATH),
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[v3.2] Cluster summary written → {SUMMARY_PATH}")
    return summary


if __name__ == "__main__":
    cluster_folios()
