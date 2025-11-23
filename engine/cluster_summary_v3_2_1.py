"""
Voynich OS v3.2.1 — Cluster Summary Builder
Builds the missing summary file required by v3.3:
    data/meaning_v3_2/cluster_summary_v3_2.json

Safe • deterministic • zero learning • public-safe.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List

REPO = Path(__file__).resolve().parents[1]
V3_2 = REPO / "data" / "meaning_v3_2"
SUMMARY = V3_2 / "cluster_summary_v3_2.json"

def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _vector_mean(vecs: List[List[float]]) -> List[float]:
    if not vecs:
        return []
    dim = len(vecs[0])
    accum = [0.0] * dim
    for v in vecs:
        for i,val in enumerate(v):
            accum[i] += val
    return [a / len(vecs) for a in accum]

def build_summary():
    cluster_groups: Dict[str, Dict] = {}
    json_files = list(V3_2.glob("F*.json"))

    for jf in json_files:
        folio = jf.stem
        data = _load_json(jf)
        cid = str(data.get("cluster_id", "none"))
        vec = data.get("vector", [])

        if cid not in cluster_groups:
            cluster_groups[cid] = {
                "cluster_id": cid,
                "folios": [],
                "vectors": [],
            }
        cluster_groups[cid]["folios"].append(folio)
        cluster_groups[cid]["vectors"].append(vec)

    # Compute stats
    summary = {}
    for cid, block in cluster_groups.items():
        summary[cid] = {
            "cluster_id": cid,
            "num_folios": len(block["folios"]),
            "folios": block["folios"],
            "mean_vector": _vector_mean(block["vectors"]),
        }

    # Write summary file
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return SUMMARY

def main():
    out = build_summary()
    print(f"Cluster summary written → {out}")

if __name__ == "__main__":
    main()
