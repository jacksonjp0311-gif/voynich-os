"""
Voynich OS — Cluster Theme Builder v3.3

Takes cluster-level structural statistics and emits:
    • cluster_theme_v3_3.json      (high-level summaries per cluster)
    • cluster_motifs_v3_3.json     (top REL/STATE motifs per cluster)
    • semantic_links_v3_3.json     (overlaps between clusters)

This module is deterministic and non-adaptive. It does NOT translate
the Voynich text; it only summarizes structural patterns derived from
REL/STATE classifiers and folio-level statistics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
MEANING_V3_2 = REPO_ROOT / "data" / "meaning_v3_2"
MEANING_V3_1 = REPO_ROOT / "data" / "meaning_v3_1"
MEANING_V3_3 = REPO_ROOT / "data" / "meaning_v3_3"

CLUSTER_SUMMARY_V3_2 = MEANING_V3_2 / "cluster_summary_v3_2.json"

THEME_PATH  = MEANING_V3_3 / "cluster_theme_v3_3.json"
MOTIFS_PATH = MEANING_V3_3 / "cluster_motifs_v3_3.json"
LINKS_PATH  = MEANING_V3_3 / "semantic_links_v3_3.json"


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _safe_get(d: Dict, key: str, default):
    v = d.get(key)
    if v is None:
        return default
    return v


def _aggregate_rel_state_for_cluster(
    folio_names: List[str],
) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    For a given list of folios (e.g. ["F1R", "F1V"]), aggregate REL and STATE
    counts from meaning_v3_1/Fxxx.json where available.
    """
    rel_counts: Dict[str, int] = {}
    state_counts: Dict[str, int] = {}

    for folio in folio_names:
        # Expect per-folio meaning JSON like data/meaning_v3_1/F1R.json
        folio_path = MEANING_V3_1 / f"{folio}.json"
        if not folio_path.exists():
            # If v3.1 snapshot not present for this folio, skip gracefully
            continue

        data = _load_json(folio_path)
        folio_rel = _safe_get(data, "rel_counts", {})
        folio_state = _safe_get(data, "state_counts", {})

        for k, v in folio_rel.items():
            rel_counts[k] = rel_counts.get(k, 0) + int(v)

        for k, v in folio_state.items():
            state_counts[k] = state_counts.get(k, 0) + int(v)

    return rel_counts, state_counts


def _top_items(counts: Dict[str, int], k: int = 8) -> List[str]:
    """
    Return up to k items sorted by frequency (descending), then by key.
    """
    items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [name for name, _ in items[:k]]


def build_cluster_motifs() -> Dict[str, Any]:
    """
    Load cluster_summary_v3_2.json and compute REL/STATE motifs for each cluster.
    Returns a mapping:
        {
            "<cluster_id>": {
                "folios": [...],
                "top_rels": [...],
                "top_states": [...],
            },
            ...
        }
    """
    summary = _load_json(CLUSTER_SUMMARY_V3_2)

    clusters = summary.get("clusters")
    if clusters is None:
        # fallback: maybe nested directly
        clusters = summary

    motifs: Dict[str, Any] = {}

    for cluster in clusters:
        cid = cluster.get("cluster_id")
        folios = cluster.get("folios", [])

        rel_counts, state_counts = _aggregate_rel_state_for_cluster(folios)
        top_rels = _top_items(rel_counts)
        top_states = _top_items(state_counts)

        motifs[str(cid)] = {
            "cluster_id": cid,
            "folios": folios,
            "num_folios": len(folios),
            "top_rels": top_rels,
            "top_states": top_states,
        }

    return motifs


def build_cluster_themes(motifs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Turn motifs into higher-level, structural theme summaries.
    These are descriptive labels, not translations.
    """
    themes: Dict[str, Any] = {}

    for cid_str, info in motifs.items():
        cid = info["cluster_id"]
        folios = info["folios"]
        top_rels = info["top_rels"]
        top_states = info["top_states"]

        # Simple structural tag set based on apparent operators/states
        tags: List[str] = []

        # REL-based tags
        if any(r.startswith("qo") or r == "REL_QO" for r in top_rels):
            tags.append("qo-dominant-operator")
        if any("ol" in r or r == "REL_OL" for r in top_rels):
            tags.append("ol-relational-band")
        if any("or" in r or r == "REL_OR" for r in top_rels):
            tags.append("or-relational-band")

        # STATE-based tags
        if any(s.endswith("Y") or s == "STATE_Y" for s in top_states):
            tags.append("y-state-heavy")
        if any("AIIN" in s.upper() or "AIN" in s.upper() for s in top_states):
            tags.append("aiin/ain-state-mass")
        if any("CHEDY" in s.upper() for s in top_states):
            tags.append("chedy-state-band")

        if not tags:
            tags.append("neutral-structural-band")

        themes[cid_str] = {
            "cluster_id": cid,
            "num_folios": len(folios),
            "folios": folios,
            "top_rels": top_rels,
            "top_states": top_states,
            "tags": tags,
            "coarse_label": f"Cluster {cid} structural theme",
        }

    return themes


def build_semantic_links(motifs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a simple overlap-based link structure between clusters.

    Two clusters are linked if they share enough REL/STATE motifs.
    """
    keys = sorted(motifs.keys(), key=lambda x: int(x))
    links: List[Dict[str, Any]] = []

    for i, a in enumerate(keys):
        for b in keys[i + 1 :]:
            ma = motifs[a]
            mb = motifs[b]

            set_rels_a = set(ma["top_rels"])
            set_rels_b = set(mb["top_rels"])
            set_states_a = set(ma["top_states"])
            set_states_b = set(mb["top_states"])

            shared_rels = sorted(set_rels_a & set_rels_b)
            shared_states = sorted(set_states_a & set_states_b)

            score = len(shared_rels) + len(shared_states)

            # Require at least 2 overlapping motifs to count as a link
            if score >= 2:
                links.append(
                    {
                        "cluster_a": int(a),
                        "cluster_b": int(b),
                        "score": score,
                        "shared_rels": shared_rels,
                        "shared_states": shared_states,
                    }
                )

    return {
        "links": links,
        "description": "Overlap-based structural links between clusters (REL/STATE motif intersections).",
    }


def run_v3_3_pipeline() -> None:
    MEANING_V3_3.mkdir(parents=True, exist_ok=True)

    motifs = build_cluster_motifs()
    themes = build_cluster_themes(motifs)
    links = build_semantic_links(motifs)

    # Write all three JSON artifacts
    with THEME_PATH.open("w", encoding="utf-8") as f:
        json.dump(themes, f, indent=2, sort_keys=True)

    with MOTIFS_PATH.open("w", encoding="utf-8") as f:
        json.dump(motifs, f, indent=2, sort_keys=True)

    with LINKS_PATH.open("w", encoding="utf-8") as f:
        json.dump(links, f, indent=2, sort_keys=True)

    print(f"Cluster themes written to: {THEME_PATH}")
    print(f"Cluster motifs written to: {MOTIFS_PATH}")
    print(f"Cluster links written to:  {LINKS_PATH}")


if __name__ == "__main__":
    run_v3_3_pipeline()
