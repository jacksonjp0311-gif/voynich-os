"""Voynich OS — Semantic Convergence Engine v3.4

Safe, deterministic global-meaning layer for Voynich OS.

Inputs
------
  • data/meaning_v3_2/cluster_summary_v3_2.json
  • data/meaning_v3_3/cluster_theme_v3_3.json
  • data/meaning_v3_3/cluster_motifs_v3_3.json
  • data/meaning_v3_3/semantic_links_v3_3.json

Outputs (under data/meaning_v3_4/)
----------------------------------
  • master_convergence_v3_4.json
  • semantic_mesh_v3_4.json
  • global_theme_map_v3_4.json
  • convergence_ledger_v3_4.jsonl

This module is:
  • Deterministic
  • Non-adaptive
  • Purely analytic (counts, groupings, aggregations)
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


REPO_ROOT = Path(__file__).resolve().parents[1]
MEANING_V32 = REPO_ROOT / "data" / "meaning_v3_2"
MEANING_V33 = REPO_ROOT / "data" / "meaning_v3_3"
OUTDIR      = REPO_ROOT / "data" / "meaning_v3_4"

CLUSTER_SUMMARY_V3_2 = MEANING_V32 / "cluster_summary_v3_2.json"
CLUSTER_THEME_V3_3   = MEANING_V33 / "cluster_theme_v3_3.json"
CLUSTER_MOTIFS_V3_3  = MEANING_V33 / "cluster_motifs_v3_3.json"
SEMANTIC_LINKS_V3_3  = MEANING_V33 / "semantic_links_v3_3.json"

MASTER_CONVERGENCE   = OUTDIR / "master_convergence_v3_4.json"
SEMANTIC_MESH        = OUTDIR / "semantic_mesh_v3_4.json"
GLOBAL_THEME_MAP     = OUTDIR / "global_theme_map_v3_4.json"
CONVERGENCE_LEDGER   = OUTDIR / "convergence_ledger_v3_4.jsonl"


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

def build_master_convergence() -> Dict[str, Any]:
    """Merge v3.2 clusters and v3.3 themes/motifs/links into one structure."""
    summary = _load_json(CLUSTER_SUMMARY_V3_2)
    themes  = _load_json(CLUSTER_THEME_V3_3)
    motifs  = _load_json(CLUSTER_MOTIFS_V3_3)
    links   = _load_json(SEMANTIC_LINKS_V3_3)

    # Try to be forgiving about schema:
    # - summary may be {"clusters":[...]} or dict-of-clusters
    clusters_raw = summary.get("clusters")
    if isinstance(clusters_raw, list):
        clusters_iter = clusters_raw
    elif isinstance(summary, dict):
        # assume mapping: cluster_id -> data
        clusters_iter = []
        for cid, cdata in summary.items():
            if isinstance(cdata, dict):
                ccopy = dict(cdata)
                ccopy.setdefault("cluster_id", cid)
                clusters_iter.append(ccopy)
    else:
        clusters_iter = []

    # Normalize theme/motif structures as dict[cluster_id] -> payload
    if isinstance(themes, list):
        theme_map = {}
        for item in themes:
            cid = str(item.get("cluster_id"))
            if cid is not None:
                theme_map[cid] = item
    elif isinstance(themes, dict):
        theme_map = themes
    else:
        theme_map = {}

    if isinstance(motifs, list):
        motif_map = {}
        for item in motifs:
            cid = str(item.get("cluster_id"))
            if cid is not None:
                motif_map[cid] = item
    elif isinstance(motifs, dict):
        motif_map = motifs
    else:
        motif_map = {}

    # Normalize links: expect list of edges with source/target cluster ids
    if isinstance(links, dict) and isinstance(links.get("links"), list):
        links_list = links["links"]
    elif isinstance(links, list):
        links_list = links
    else:
        links_list = []

    cluster_entries: List[Dict[str, Any]] = []
    theme_frequency: Dict[str, int] = {}

    for c in clusters_iter:
        cid = str(c.get("cluster_id"))
        theme_info = theme_map.get(cid, {})
        motif_info = motif_map.get(cid, {})

        theme_label = theme_info.get("theme_label") or theme_info.get("label") or "UNKNOWN"

        # Count theme usage
        theme_frequency[theme_label] = theme_frequency.get(theme_label, 0) + 1

        entry = {
            "cluster_id": cid,
            "size": c.get("size"),
            "folios": c.get("folios") or c.get("folio_ids") or [],
            "centroid": c.get("centroid"),
            "theme_label": theme_label,
            "theme_data": theme_info,
            "motifs": motif_info.get("motifs") or motif_info.get("top_motifs") or [],
        }
        cluster_entries.append(entry)

    master = {
        "meta": {
            "version": "3.4",
            "description": "Global convergence of clusters, themes, motifs, and links.",
        },
        "theme_frequency": theme_frequency,
        "clusters": cluster_entries,
        "links": links_list,
    }
    return master


def build_semantic_mesh(master: Dict[str, Any]) -> Dict[str, Any]:
    """Build a simple bipartite mesh: theme nodes + cluster nodes + edges."""
    theme_nodes: Dict[str, Dict[str, Any]] = {}
    cluster_nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []

    for cluster in master.get("clusters", []):
        cid = str(cluster.get("cluster_id"))
        theme_label = cluster.get("theme_label", "UNKNOWN")

        # theme node
        if theme_label not in theme_nodes:
            theme_nodes[theme_label] = {
                "id": theme_label,
                "type": "theme",
                "count_clusters": 0,
            }
        theme_nodes[theme_label]["count_clusters"] += 1

        # cluster node
        if cid not in cluster_nodes:
            cluster_nodes[cid] = {
                "id": cid,
                "type": "cluster",
                "size": cluster.get("size"),
                "folios": cluster.get("folios", []),
            }

        # bipartite edge theme <-> cluster
        edges.append(
            {
                "source": theme_label,
                "target": cid,
                "relation": "belongs_to_theme",
            }
        )

    # Also project cluster-to-cluster links through themes
    for link in master.get("links", []):
        src = str(link.get("source_cluster") or link.get("source") or "")
        tgt = str(link.get("target_cluster") or link.get("target") or "")
        if not src or not tgt:
            continue
        weight = link.get("weight", 1.0)
        relation = link.get("relation") or "semantic_link"

        edges.append(
            {
                "source": src,
                "target": tgt,
                "relation": relation,
                "weight": weight,
            }
        )

    mesh = {
        "meta": {
            "version": "3.4",
            "description": "Theme/cluster semantic mesh for Voynich OS.",
        },
        "themes": list(theme_nodes.values()),
        "clusters": list(cluster_nodes.values()),
        "edges": edges,
    }
    return mesh


def build_global_theme_map(master: Dict[str, Any]) -> Dict[str, Any]:
    """Collapse cluster-level info into a per-theme summary."""
    theme_map: Dict[str, Dict[str, Any]] = {}

    for cluster in master.get("clusters", []):
        theme_label = cluster.get("theme_label", "UNKNOWN")
        cid = str(cluster.get("cluster_id"))
        folios = cluster.get("folios", [])
        motifs = cluster.get("motifs", [])

        if theme_label not in theme_map:
            theme_map[theme_label] = {
                "theme_label": theme_label,
                "clusters": [],
                "folios": [],
                "motifs": [],
            }

        t = theme_map[theme_label]
        t["clusters"].append(cid)

        for f in folios:
            if f not in t["folios"]:
                t["folios"].append(f)

        for m in motifs:
            if m not in t["motifs"]:
                t["motifs"].append(m)

    return {
        "meta": {
            "version": "3.4",
            "description": "Global theme map (clusters + folios + motifs).",
        },
        "themes": list(theme_map.values()),
    }


def run_v3_4_pipeline() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    master = build_master_convergence()
    mesh   = build_semantic_mesh(master)
    gmap   = build_global_theme_map(master)

    _write_json(MASTER_CONVERGENCE, master)
    _write_json(SEMANTIC_MESH, mesh)
    _write_json(GLOBAL_THEME_MAP, gmap)

    # Simple ledger entry
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "3.4",
        "num_clusters": len(master.get("clusters", [])),
        "num_links": len(master.get("links", [])),
        "num_themes": len(gmap.get("themes", [])),
    }
    _append_ledger_entry(CONVERGENCE_LEDGER, entry)

    print(f"Master convergence → {MASTER_CONVERGENCE}")
    print(f"Semantic mesh      → {SEMANTIC_MESH}")
    print(f"Global theme map   → {GLOBAL_THEME_MAP}")
    print(f"Ledger append      → {CONVERGENCE_LEDGER}")


if __name__ == "__main__":
    run_v3_4_pipeline()
