"""
Voynich OS — Cross-Folio Meaning Engine v3.2

Pipeline:
    1) Build per-folio structural vectors (page_vectorizer)
    2) Cluster folios into structural families (folio_cluster)

Outputs live under:
    data/meaning_v3_2/
"""

from __future__ import annotations
from pathlib import Path

from . import page_vectorizer
from . import folio_cluster


def run_pipeline() -> None:
    root = Path(__file__).resolve().parents[1]
    meaning_root = root / "data" / "meaning_v3_2"
    meaning_root.mkdir(parents=True, exist_ok=True)

    print("[v3.2] Step 1 — Building page vectors...")
    index = page_vectorizer.build_all_page_vectors()
    print(f"[v3.2]   Page vectors built for {len(index)} folios.")

    print("[v3.2] Step 2 — Clustering folios...")
    summary = folio_cluster.cluster_folios()
    print("[v3.2]   Clustering done.")
    print(f"[v3.2]   Summary at: {summary and meaning_root / 'clusters' / 'cluster_summary_v3_2.json'}")


if __name__ == "__main__":
    run_pipeline()
