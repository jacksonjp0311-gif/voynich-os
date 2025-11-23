"""Voynich OS — Meaning Atlas Engine v3.7

Safe, deterministic global meaning atlas for Voynich OS.

Inputs
------
  • data/meaning_v3_4/semantic_mesh_v3_4.json
      - theme + cluster nodes and edges
  • data/meaning_v3_4/master_convergence_v3_4.json
      - clusters, themes, motifs, links
  • data/meaning_v3_5/meaning_index_v3_5.json
      - per-folio dominant theme, top themes, motifs, etc.
  • data/meaning_v3_6/continuity_graph_v3_6.json
      - folio continuity nodes/edges
  • data/meaning_v3_6/meaning_flow_v3_6.json
      - continuity statistics and segments

Outputs (under data/meaning_v3_7/)
----------------------------------
  • atlas_graph_v3_7.json
       - combined graph of themes, clusters, folios, and edges
  • meaning_atlas_v3_7.json
       - summary of global themes, folio roles, and continuity
  • atlas_legend_v3_7.json
       - legend for downstream visualization / UI
  • meaning_atlas_ledger_v3_7.jsonl
       - append-only ledger of v3.7 runs

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

MEANING_V34 = REPO_ROOT / "data" / "meaning_v3_4"
MEANING_V35 = REPO_ROOT / "data" / "meaning_v3_5"
MEANING_V36 = REPO_ROOT / "data" / "meaning_v3_6"
OUTDIR      = REPO_ROOT / "data" / "meaning_v3_7"

SEMANTIC_MESH       = MEANING_V34 / "semantic_mesh_v3_4.json"
MASTER_CONVERGENCE  = MEANING_V34 / "master_convergence_v3_4.json"
MEANING_INDEX       = MEANING_V35 / "meaning_index_v3_5.json"
CONTINUITY_GRAPH    = MEANING_V36 / "continuity_graph_v3_6.json"
MEANING_FLOW        = MEANING_V36 / "meaning_flow_v3_6.json"

ATLAS_GRAPH   = OUTDIR / "atlas_graph_v3_7.json"
ATLAS_SUMMARY = OUTDIR / "meaning_atlas_v3_7.json"
ATLAS_LEGEND  = OUTDIR / "atlas_legend_v3_7.json"
ATLAS_LEDGER  = OUTDIR / "meaning_atlas_ledger_v3_7.jsonl"


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


# ────────────────────────────────────────────────────────────────────
# Node builders
# ────────────────────────────────────────────────────────────────────

def build_theme_cluster_nodes_and_edges(
    semantic_mesh: Dict[str, Any]
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Build theme + cluster node maps and theme<->cluster edges from semantic_mesh_v3_4.

    Expects semantic_mesh = {
      "themes": [...],
      "clusters": [...],
      "edges": [...]
    }
    """
    themes_raw = semantic_mesh.get("themes") or []
    clusters_raw = semantic_mesh.get("clusters") or []
    edges_raw = semantic_mesh.get("edges") or []

    theme_nodes: Dict[str, Dict[str, Any]] = {}
    cluster_nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []

    # Theme nodes
    for t in themes_raw:
        tid = str(t.get("id") or t.get("theme_label") or t.get("label") or "")
        if not tid:
            continue
        node = {
            "id": tid,
            "type": "theme",
        }
        # carry over basic fields
        for k, v in t.items():
            if k in ("id", "type"):
                continue
            node[k] = v
        theme_nodes[tid] = node

    # Cluster nodes
    for c in clusters_raw:
        cid = str(c.get("id") or c.get("cluster_id") or "")
        if not cid:
            continue
        node = {
            "id": cid,
            "type": "cluster",
        }
        for k, v in c.items():
            if k in ("id", "type"):
                continue
            node[k] = v
        cluster_nodes[cid] = node

    # Edges (mostly theme<->cluster from mesh)
    for e in edges_raw:
        src = e.get("source")
        tgt = e.get("target")
        if not src or not tgt:
            continue
        edge = {
            "source": str(src),
            "target": str(tgt),
            "relation": e.get("relation") or "mesh_link",
        }
        if "continuity_score" in e:
            edge["continuity_score"] = _safe_float(e["continuity_score"])
        if "weight" in e:
            edge["weight"] = _safe_float(e["weight"])
        edges.append(edge)

    return theme_nodes, cluster_nodes, edges


def build_cluster_folio_edges_from_master(
    master: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Build cluster<->folio edges from master_convergence_v3_4.
    master["clusters"] entries expected to have "cluster_id" and "folios" list.
    """
    clusters = master.get("clusters", [])
    edges: List[Dict[str, Any]] = []

    for c in clusters:
        cid = str(c.get("cluster_id"))
        folios = c.get("folios") or c.get("folio_ids") or []
        for folio_id in folios:
            fid = str(folio_id)
            if not fid:
                continue
            edges.append(
                {
                    "source": cid,
                    "target": fid,
                    "relation": "appears_in_folio",
                }
            )
    return edges


def build_folio_nodes_and_theme_edges(
    meaning_index: Dict[str, Any]
) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
    """
    Build folio nodes and theme->folio edges from meaning_index_v3_5.
    Also track how often each theme is dominant.
    """
    folios = meaning_index.get("folios") or meaning_index.get("data") or []
    folio_nodes: Dict[str, Dict[str, Any]] = {}
    theme_dominance_counts: Dict[str, int] = {}
    theme_to_folio_edges: List[Dict[str, Any]] = []

    for entry in folios:
        fid = str(entry.get("folio_id"))
        if not fid:
            continue

        dom_theme = entry.get("dominant_theme") or "UNKNOWN"
        dom_score = _safe_float(entry.get("dominant_score"))
        node = {
            "id": fid,
            "type": "folio",
            "dominant_theme": dom_theme,
            "dominant_score": dom_score,
            "num_clusters": int(entry.get("num_clusters") or 0),
            "num_motifs": int(entry.get("num_motifs") or 0),
            "cross_link_degree": _safe_float(entry.get("cross_link_degree")),
        }
        folio_nodes[fid] = node

        theme_dominance_counts[dom_theme] = theme_dominance_counts.get(dom_theme, 0) + 1

        theme_to_folio_edges.append(
            {
                "source": dom_theme,
                "target": fid,
                "relation": "dominant_theme_for",
                "weight": dom_score,
            }
        )

    return folio_nodes, theme_to_folio_edges, theme_dominance_counts


def build_folio_folio_edges_from_continuity(
    continuity_graph: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Convert continuity_graph_v3_6 edges into folio<->folio edges.
    """
    edges_raw = continuity_graph.get("edges", [])
    edges: List[Dict[str, Any]] = []

    for e in edges_raw:
        src = e.get("source")
        tgt = e.get("target")
        if not src or not tgt:
            continue
        edges.append(
            {
                "source": str(src),
                "target": str(tgt),
                "relation": "folio_continuity",
                "continuity_score": _safe_float(e.get("continuity_score")),
                "theme_overlap_score": _safe_float(e.get("theme_overlap_score")),
                "motif_overlap_score": _safe_float(e.get("motif_overlap_score")),
            }
        )
    return edges


# ────────────────────────────────────────────────────────────────────
# Summary builders
# ────────────────────────────────────────────────────────────────────

def build_atlas_summary(
    theme_nodes: Dict[str, Dict[str, Any]],
    cluster_nodes: Dict[str, Dict[str, Any]],
    folio_nodes: Dict[str, Dict[str, Any]],
    theme_dominance_counts: Dict[str, int],
    meaning_flow: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build global atlas summary: counts, top themes, and continuity snapshot.
    """
    num_themes = len(theme_nodes)
    num_clusters = len(cluster_nodes)
    num_folios = len(folio_nodes)

    # Top dominant themes by how many folios they dominate
    top_theme_items = sorted(
        theme_dominance_counts.items(),
        key=lambda kv: kv[1],
        reverse=True,
    )
    top_themes = [
        {"theme_label": label, "num_dominant_folios": count}
        for label, count in top_theme_items[:10]
    ]

    flow_stats = meaning_flow.get("stats", {}) if isinstance(meaning_flow, dict) else {}
    hotspots = meaning_flow.get("hotspots", []) if isinstance(meaning_flow, dict) else []
    segments = meaning_flow.get("high_continuity_segments", []) if isinstance(meaning_flow, dict) else []

    meta = {
        "version": "3.7",
        "description": "Global meaning atlas summary (themes, clusters, folios, continuity).",
    }

    return {
        "meta": meta,
        "counts": {
            "num_themes": num_themes,
            "num_clusters": num_clusters,
            "num_folios": num_folios,
        },
        "top_dominant_themes": top_themes,
        "continuity_stats": flow_stats,
        "continuity_hotspots": hotspots,
        "high_continuity_segments": segments,
    }


def build_atlas_legend() -> Dict[str, Any]:
    """
    Provide a human-readable legend for the atlas graph structure,
    to help downstream visualization / UI tools interpret the JSON.
    """
    return {
        "meta": {
            "version": "3.7",
            "description": "Legend for atlas_graph_v3_7.json and meaning_atlas_v3_7.json.",
        },
        "node_types": {
            "theme": "Represents a semantic theme label derived from cluster + motif analysis.",
            "cluster": "Represents a cluster of folios in meaning-space.",
            "folio": "Represents an individual Voynich folio (e.g., F1R, F42V).",
        },
        "edge_types": {
            "mesh_link": "Generic edge from semantic_mesh_v3_4 (theme–cluster relationships).",
            "belongs_to_theme": "Cluster belongs to a given theme (if present in semantic_mesh).",
            "appears_in_folio": "Cluster appears in the given folio.",
            "dominant_theme_for": "Theme is the dominant theme for the given folio.",
            "folio_continuity": "Adjacency between folios with continuity scores (from v3.6).",
        },
        "continuity_fields": {
            "continuity_score": "Weighted combination of theme + motif overlap between adjacent folios.",
            "theme_overlap_score": "Normalized overlap of theme-score vectors.",
            "motif_overlap_score": "Normalized overlap of motif-count vectors.",
        },
        "atlas_files": {
            "atlas_graph_v3_7.json": "Full node/edge graph of themes, clusters, and folios.",
            "meaning_atlas_v3_7.json": "High-level summary of themes, continuity, and hotspots.",
            "atlas_legend_v3_7.json": "This legend file.",
        },
    }


# ────────────────────────────────────────────────────────────────────
# Pipeline
# ────────────────────────────────────────────────────────────────────

def run_v3_7_pipeline() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    semantic_mesh = _load_json(SEMANTIC_MESH)
    master = _load_json(MASTER_CONVERGENCE)
    meaning_index = _load_json(MEANING_INDEX)
    continuity_graph = _load_json(CONTINUITY_GRAPH)

    try:
        meaning_flow = _load_json(MEANING_FLOW)
    except FileNotFoundError:
        meaning_flow = {}

    # Nodes and edges from different layers
    theme_nodes, cluster_nodes, theme_cluster_edges = build_theme_cluster_nodes_and_edges(
        semantic_mesh
    )
    cluster_folio_edges = build_cluster_folio_edges_from_master(master)
    folio_nodes, theme_folio_edges, theme_dominance_counts = build_folio_nodes_and_theme_edges(
        meaning_index
    )
    folio_folio_edges = build_folio_folio_edges_from_continuity(continuity_graph)

    # Combine nodes
    all_nodes_map: Dict[str, Dict[str, Any]] = {}
    all_nodes_map.update(theme_nodes)
    all_nodes_map.update(cluster_nodes)
    all_nodes_map.update(folio_nodes)
    all_nodes = list(all_nodes_map.values())

    # Combine edges
    all_edges: List[Dict[str, Any]] = []
    all_edges.extend(theme_cluster_edges)
    all_edges.extend(cluster_folio_edges)
    all_edges.extend(theme_folio_edges)
    all_edges.extend(folio_folio_edges)

    atlas_graph = {
        "meta": {
            "version": "3.7",
            "description": "Combined meaning atlas graph (themes, clusters, folios).",
        },
        "nodes": all_nodes,
        "edges": all_edges,
    }

    atlas_summary = build_atlas_summary(
        theme_nodes=theme_nodes,
        cluster_nodes=cluster_nodes,
        folio_nodes=folio_nodes,
        theme_dominance_counts=theme_dominance_counts,
        meaning_flow=meaning_flow,
    )

    atlas_legend = build_atlas_legend()

    _write_json(ATLAS_GRAPH, atlas_graph)
    _write_json(ATLAS_SUMMARY, atlas_summary)
    _write_json(ATLAS_LEGEND, atlas_legend)

    # Ledger entry
    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": ts,
        "version": "3.7",
        "num_nodes": len(all_nodes),
        "num_edges": len(all_edges),
        "num_themes": len(theme_nodes),
        "num_clusters": len(cluster_nodes),
        "num_folios": len(folio_nodes),
    }
    _append_ledger_entry(ATLAS_LEDGER, entry)

    print(f"Atlas graph    → {ATLAS_GRAPH}")
    print(f"Atlas summary  → {ATLAS_SUMMARY}")
    print(f"Atlas legend   → {ATLAS_LEGEND}")
    print(f"Ledger append  → {ATLAS_LEDGER}")


if __name__ == "__main__":
    run_v3_7_pipeline()
