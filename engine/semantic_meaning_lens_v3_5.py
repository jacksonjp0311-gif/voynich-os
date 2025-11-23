"""Voynich OS — Meaning Lens Engine v3.5

Safe, deterministic folio meaning projection for Voynich OS.

Inputs
------
  • data/meaning_v3_4/master_convergence_v3_4.json

Outputs (under data/meaning_v3_5/)
----------------------------------
  • folios/<FOLIO>.json           (per-folio meaning lens)
  • meaning_index_v3_5.json       (global folio meaning index)
  • meaning_ledger_v3_5.jsonl     (append-only log)

This module is:
  • Deterministic
  • Non-adaptive
  • Purely analytic (counts, groupings, aggregations)

Interpretation
--------------
Each folio accumulates:
  • clusters it belongs to
  • themes associated with those clusters (with weights)
  • motifs appearing in those clusters
  • a simple cross-link degree via cluster links

We then compute a normalized "meaning profile" per folio:
  • dominant theme
  • top themes (with scores)
  • top motifs (with counts)
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone


REPO_ROOT = Path(__file__).resolve().parents[1]

MEANING_V34 = REPO_ROOT / "data" / "meaning_v3_4"
OUTDIR      = REPO_ROOT / "data" / "meaning_v3_5"
FOLIO_DIR   = OUTDIR / "folios"

MASTER_CONVERGENCE = MEANING_V34 / "master_convergence_v3_4.json"
MEANING_INDEX      = OUTDIR / "meaning_index_v3_5.json"
MEANING_LEDGER     = OUTDIR / "meaning_ledger_v3_5.jsonl"


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


# ────────────────────────────────────────────────────────────────────
# Core logic
# ────────────────────────────────────────────────────────────────────

def build_folio_meaning(master: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Build per-folio meaning profiles from the master convergence structure.

    master["clusters"] entries are expected to have:
      - "cluster_id"
      - "theme_label"
      - "motifs"
      - "folios"
    master["links"] entries optionally connect clusters.
    """
    clusters = master.get("clusters", [])
    links    = master.get("links", [])

    # Precompute cluster link degree (how connected each cluster is).
    cluster_degree: Dict[str, int] = {}
    for link in links:
        src = str(link.get("source_cluster") or link.get("source") or "")
        tgt = str(link.get("target_cluster") or link.get("target") or "")
        if not src or not tgt:
            continue
        if src not in cluster_degree:
            cluster_degree[src] = 0
        if tgt not in cluster_degree:
            cluster_degree[tgt] = 0
        cluster_degree[src] += 1
        cluster_degree[tgt] += 1

    folio_map: Dict[str, Dict[str, Any]] = {}

    for c in clusters:
        cid = str(c.get("cluster_id"))
        theme_label = c.get("theme_label", "UNKNOWN")
        motifs = c.get("motifs", []) or []
        folios = c.get("folios", []) or []

        # cluster contributes weight 1 to its theme for each folio
        for folio_id in folios:
            folio_id = str(folio_id)

            if folio_id not in folio_map:
                folio_map[folio_id] = {
                    "folio_id": folio_id,
                    "clusters": [],
                    "theme_counts": {},
                    "motif_counts": {},
                    "cluster_degree_sum": 0,
                }

            f = folio_map[folio_id]

            # record cluster membership (dedup)
            if cid not in f["clusters"]:
                f["clusters"].append(cid)

            # increment theme count
            theme_counts = f["theme_counts"]
            theme_counts[theme_label] = theme_counts.get(theme_label, 0) + 1

            # increment motif counts
            motif_counts = f["motif_counts"]
            for m in motifs:
                motif_counts[m] = motif_counts.get(m, 0) + 1

            # accumulate cluster degree (if any)
            if cid in cluster_degree:
                f["cluster_degree_sum"] += cluster_degree[cid]

    # Normalize themes into score vectors and compute derived metrics.
    for folio_id, f in folio_map.items():
        theme_counts = f["theme_counts"]
        total_theme_weight = sum(theme_counts.values()) or 1

        # Build sorted list of (theme, score, raw_count)
        theme_list: List[Dict[str, Any]] = []
        for theme_label, count in theme_counts.items():
            score = float(count) / float(total_theme_weight)
            theme_list.append(
                {
                    "theme_label": theme_label,
                    "score": score,
                    "count": count,
                }
            )
        theme_list.sort(key=lambda x: x["score"], reverse=True)

        # Top motifs by raw frequency
        motif_counts = f["motif_counts"]
        motifs_sorted = sorted(
            [{"motif": m, "count": c} for m, c in motif_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )

        dominant_theme = theme_list[0]["theme_label"] if theme_list else "UNKNOWN"
        dominant_score = theme_list[0]["score"] if theme_list else 0.0

        f["dominant_theme"] = dominant_theme
        f["dominant_score"] = dominant_score
        f["themes_ranked"] = theme_list
        f["motifs_ranked"] = motifs_sorted
        f["num_clusters"] = len(f["clusters"])
        f["num_motifs"] = len(motif_counts)
        f["cross_link_degree"] = f["cluster_degree_sum"]

    return folio_map


def write_per_folio_files(folio_map: Dict[str, Dict[str, Any]]) -> None:
    """
    Write one JSON file per folio under data/meaning_v3_5/folios.
    """
    FOLIO_DIR.mkdir(parents=True, exist_ok=True)
    for folio_id, payload in folio_map.items():
        out_path = FOLIO_DIR / f"{folio_id}.json"
        _write_json(out_path, payload)


def build_meaning_index(folio_map: Dict[str, Dict[str, Any]], master: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a compact global index summarizing folio-level meaning.
    """
    folio_summaries: List[Dict[str, Any]] = []

    for folio_id, f in sorted(folio_map.items(), key=lambda kv: kv[0]):
        top_themes = f.get("themes_ranked", [])[:5]
        top_motifs = f.get("motifs_ranked", [])[:5]

        folio_summaries.append(
            {
                "folio_id": folio_id,
                "dominant_theme": f.get("dominant_theme"),
                "dominant_score": f.get("dominant_score"),
                "num_clusters": f.get("num_clusters"),
                "num_motifs": f.get("num_motifs"),
                "cross_link_degree": f.get("cross_link_degree"),
                "top_themes": top_themes,
                "top_motifs": top_motifs,
            }
        )

    meta = {
        "version": "3.5",
        "description": "Per-folio semantic meaning index derived from v3.4 master convergence.",
        "source_master_convergence": str(MASTER_CONVERGENCE),
        "num_folios": len(folio_summaries),
        "num_clusters": len(master.get("clusters", [])),
        "num_links": len(master.get("links", [])),
    }

    return {
        "meta": meta,
        "folios": folio_summaries,
    }


def run_v3_5_pipeline() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    FOLIO_DIR.mkdir(parents=True, exist_ok=True)

    master = _load_json(MASTER_CONVERGENCE)

    folio_map = build_folio_meaning(master)
    write_per_folio_files(folio_map)

    index = build_meaning_index(folio_map, master)
    _write_json(MEANING_INDEX, index)

    # Ledger entry
    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": ts,
        "version": "3.5",
        "num_folios": len(index.get("folios", [])),
        "num_clusters": len(master.get("clusters", [])),
        "num_links": len(master.get("links", [])),
    }
    _append_ledger_entry(MEANING_LEDGER, entry)

    print(f"Per-folio meaning → {FOLIO_DIR}")
    print(f"Meaning index     → {MEANING_INDEX}")
    print(f"Ledger append     → {MEANING_LEDGER}")


if __name__ == "__main__":
    run_v3_5_pipeline()
