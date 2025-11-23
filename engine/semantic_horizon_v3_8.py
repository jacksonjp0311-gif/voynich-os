"""Voynich OS — Semantic Horizon Engine v3.8

Safe, deterministic semantic horizon field for Voynich OS.

Inputs
------
  • data/meaning_v3_7/atlas_graph_v3_7.json
      - combined graph of themes, clusters, folios, continuity edges
  • data/meaning_v3_7/meaning_atlas_v3_7.json
      - global atlas summary & continuity stats
  • data/meaning_v3_6/meaning_flow_v3_6.json
      - continuity distribution, hotspots, high-continuity segments
  • data/meaning_v3_5/meaning_index_v3_5.json
      - per-folio dominant theme, top themes, motifs, etc.

Outputs (under data/meaning_v3_8/)
----------------------------------
  • semantic_horizon_v3_8.json
       - per-folio, per-theme, and per-cluster horizon metrics
  • horizon_map_v3_8.json
       - global horizon field & distributions
  • horizon_intersections_v3_8.json
       - folio / cluster positions where themes intersect strongly
  • meaning_pressure_v3_8.json
       - theme + cluster “pressure” scoreboard
  • horizon_ledger_v3_8.jsonl
       - append-only ledger of v3.8 runs

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

MEANING_V37 = REPO_ROOT / "data" / "meaning_v3_7"
MEANING_V36 = REPO_ROOT / "data" / "meaning_v3_6"
MEANING_V35 = REPO_ROOT / "data" / "meaning_v3_5"
OUTDIR      = REPO_ROOT / "data" / "meaning_v3_8"

ATLAS_GRAPH   = MEANING_V37 / "atlas_graph_v3_7.json"
ATLAS_SUMMARY = MEANING_V37 / "meaning_atlas_v3_7.json"
MEANING_FLOW  = MEANING_V36 / "meaning_flow_v3_6.json"
MEANING_INDEX = MEANING_V35 / "meaning_index_v3_5.json"

SEMANTIC_HORIZON     = OUTDIR / "semantic_horizon_v3_8.json"
HORIZON_MAP          = OUTDIR / "horizon_map_v3_8.json"
HORIZON_INTERSECTIONS= OUTDIR / "horizon_intersections_v3_8.json"
MEANING_PRESSURE     = OUTDIR / "meaning_pressure_v3_8.json"
HORIZON_LEDGER       = OUTDIR / "horizon_ledger_v3_8.jsonl"


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


def _safe_int(x: Any) -> int:
    try:
        return int(x)
    except Exception:
        return 0


# ────────────────────────────────────────────────────────────────────
# Core extraction from existing layers
# ────────────────────────────────────────────────────────────────────

def _build_folio_summary_map(meaning_index: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """folio_id -> summary entry from meaning_index_v3_5."""
    folios = meaning_index.get("folios") or meaning_index.get("data") or []
    out: Dict[str, Dict[str, Any]] = {}
    for entry in folios:
        fid = str(entry.get("folio_id"))
        if not fid:
            continue
        out[fid] = entry
    return out


def _build_hotspot_sets(meaning_flow: Dict[str, Any]) -> Dict[str, set]:
    """
    Return:
      - hotspot_folios: folios that sit on low-continuity boundaries
      - high_seg_folios: folios inside high-continuity segments
    """
    hotspot_folios = set()
    high_seg_folios = set()

    hotspots = meaning_flow.get("hotspots", []) if isinstance(meaning_flow, dict) else []
    for h in hotspots:
        fa = str(h.get("from_folio"))
        fb = str(h.get("to_folio"))
        if fa:
            hotspot_folios.add(fa)
        if fb:
            hotspot_folios.add(fb)

    segments = meaning_flow.get("high_continuity_segments", []) if isinstance(meaning_flow, dict) else []
    for seg in segments:
        fa = str(seg.get("from_folio"))
        fb = str(seg.get("to_folio"))
        if fa:
            high_seg_folios.add(fa)
        if fb:
            high_seg_folios.add(fb)

    return {
        "hotspot_folios": hotspot_folios,
        "high_seg_folios": high_seg_folios,
    }


def _partition_edges_by_relation(atlas_graph: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    edges_raw = atlas_graph.get("edges", []) or []
    by_rel: Dict[str, List[Dict[str, Any]]] = {}
    for e in edges_raw:
        rel = e.get("relation") or "mesh_link"
        by_rel.setdefault(rel, []).append(e)
    return by_rel


def _build_folio_continuity_stats(
    folio_map: Dict[str, Dict[str, Any]],
    continuity_edges: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    For each folio, aggregate continuity edges that touch it and compute:
      • degree
      • avg/min/max continuity_score
      • avg theme_overlap_score
      • avg motif_overlap_score
    """
    per_folio: Dict[str, Dict[str, Any]] = {fid: {
        "degree": 0,
        "continuity_scores": [],
        "theme_scores": [],
        "motif_scores": [],
    } for fid in folio_map.keys()}

    for e in continuity_edges:
        src = str(e.get("source"))
        tgt = str(e.get("target"))
        cs  = _safe_float(e.get("continuity_score"))
        ts  = _safe_float(e.get("theme_overlap_score"))
        ms  = _safe_float(e.get("motif_overlap_score"))
        for fid in (src, tgt):
            if fid in per_folio:
                rec = per_folio[fid]
                rec["degree"] += 1
                rec["continuity_scores"].append(cs)
                rec["theme_scores"].append(ts)
                rec["motif_scores"].append(ms)

    out: Dict[str, Dict[str, Any]] = {}
    for fid, rec in per_folio.items():
        scores = rec["continuity_scores"]
        tscores = rec["theme_scores"]
        mscores = rec["motif_scores"]

        if scores:
            avg_c = sum(scores) / float(len(scores))
            min_c = min(scores)
            max_c = max(scores)
        else:
            avg_c = 0.0
            min_c = 0.0
            max_c = 0.0

        if tscores:
            avg_t = sum(tscores) / float(len(tscores))
        else:
            avg_t = 0.0

        if mscores:
            avg_m = sum(mscores) / float(len(mscores))
        else:
            avg_m = 0.0

        out[fid] = {
            "continuity_degree": rec["degree"],
            "continuity_avg": avg_c,
            "continuity_min": min_c,
            "continuity_max": max_c,
            "theme_overlap_avg": avg_t,
            "motif_overlap_avg": avg_m,
        }

    return out


def _build_cluster_to_folios(cluster_folio_edges: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    m: Dict[str, List[str]] = {}
    for e in cluster_folio_edges:
        cid = str(e.get("source"))
        fid = str(e.get("target"))
        if not cid or not fid:
            continue
        m.setdefault(cid, []).append(fid)
    return m


# ────────────────────────────────────────────────────────────────────
# Horizon builders
# ────────────────────────────────────────────────────────────────────

def build_semantic_horizon(
    atlas_graph: Dict[str, Any],
    atlas_summary: Dict[str, Any],
    meaning_flow: Dict[str, Any],
    meaning_index: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build the core semantic horizon structure:
      - per_folio horizon metrics
      - theme-level horizon metrics
      - cluster-level horizon metrics
    """
    folio_map = _build_folio_summary_map(meaning_index)
    hotsets = _build_hotspot_sets(meaning_flow)
    hotspot_folios = hotsets["hotspot_folios"]
    high_seg_folios = hotsets["high_seg_folios"]

    edges_by_rel = _partition_edges_by_relation(atlas_graph)
    continuity_edges = edges_by_rel.get("folio_continuity", [])
    cluster_folio_edges = edges_by_rel.get("appears_in_folio", [])
    theme_folio_edges = edges_by_rel.get("dominant_theme_for", [])

    # Per-folio continuity stats
    continuity_stats = _build_folio_continuity_stats(folio_map, continuity_edges)

    # Per-folio horizon block
    per_folio: List[Dict[str, Any]] = []
    for fid, entry in folio_map.items():
        cstats = continuity_stats.get(fid, {})
        dom_theme = entry.get("dominant_theme") or "UNKNOWN"
        dom_score = _safe_float(entry.get("dominant_score"))
        num_clusters = _safe_int(entry.get("num_clusters"))
        num_motifs = _safe_int(entry.get("num_motifs"))
        cross_link_degree = _safe_float(entry.get("cross_link_degree"))

        local_theme_pressure = dom_score * max(1, num_clusters)
        local_motif_density = float(num_motifs)

        per_folio.append(
            {
                "folio_id": fid,
                "dominant_theme": dom_theme,
                "dominant_score": dom_score,
                "num_clusters": num_clusters,
                "num_motifs": num_motifs,
                "cross_link_degree": cross_link_degree,
                "continuity_degree": cstats.get("continuity_degree", 0),
                "continuity_avg": cstats.get("continuity_avg", 0.0),
                "continuity_min": cstats.get("continuity_min", 0.0),
                "continuity_max": cstats.get("continuity_max", 0.0),
                "theme_overlap_avg": cstats.get("theme_overlap_avg", 0.0),
                "motif_overlap_avg": cstats.get("motif_overlap_avg", 0.0),
                "local_theme_pressure": local_theme_pressure,
                "local_motif_density": local_motif_density,
                "is_hotspot_boundary": (fid in hotspot_folios),
                "is_high_continuity_zone": (fid in high_seg_folios),
            }
        )

    # Theme-level horizon metrics
    theme_horizon: Dict[str, Dict[str, Any]] = {}
    for f in per_folio:
        theme = f["dominant_theme"]
        th = theme_horizon.setdefault(
            theme,
            {
                "theme_label": theme,
                "num_dominant_folios": 0,
                "sum_continuity_avg": 0.0,
                "sum_continuity_degree": 0.0,
                "sum_theme_pressure": 0.0,
                "hotspot_folios": 0,
                "high_zone_folios": 0,
            },
        )
        th["num_dominant_folios"] += 1
        th["sum_continuity_avg"] += f["continuity_avg"]
        th["sum_continuity_degree"] += f["continuity_degree"]
        th["sum_theme_pressure"] += f["local_theme_pressure"]
        if f["is_hotspot_boundary"]:
            th["hotspot_folios"] += 1
        if f["is_high_continuity_zone"]:
            th["high_zone_folios"] += 1

    for theme, th in theme_horizon.items():
        n = th["num_dominant_folios"] or 1
        th["avg_continuity"] = th["sum_continuity_avg"] / float(n)
        th["avg_continuity_degree"] = th["sum_continuity_degree"] / float(n)
        th["avg_theme_pressure"] = th["sum_theme_pressure"] / float(n)

    # Cluster-level horizon metrics
    cluster_to_folios = _build_cluster_to_folios(cluster_folio_edges)
    folio_cont_map = {f["folio_id"]: f["continuity_avg"] for f in per_folio}
    folio_theme_map = {f["folio_id"]: f["dominant_theme"] for f in per_folio}

    cluster_horizon: List[Dict[str, Any]] = []
    for cid, folios in cluster_to_folios.items():
        unique_folios = sorted(set(folios))
        continuity_vals = [folio_cont_map.get(fid, 0.0) for fid in unique_folios]
        themes = {folio_theme_map.get(fid, "UNKNOWN") for fid in unique_folios}

        if continuity_vals:
            avg_c = sum(continuity_vals) / float(len(continuity_vals))
            min_c = min(continuity_vals)
            max_c = max(continuity_vals)
        else:
            avg_c = 0.0
            min_c = 0.0
            max_c = 0.0

        cluster_horizon.append(
            {
                "cluster_id": cid,
                "num_folios": len(unique_folios),
                "folios": unique_folios,
                "theme_diversity": len(themes),
                "themes": sorted(themes),
                "continuity_avg": avg_c,
                "continuity_min": min_c,
                "continuity_max": max_c,
            }
        )

    return {
        "meta": {
            "version": "3.8",
            "description": "Semantic horizon metrics across folios, themes, and clusters.",
        },
        "per_folio": per_folio,
        "themes": list(theme_horizon.values()),
        "clusters": cluster_horizon,
    }


def build_horizon_map(semantic_horizon: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build global horizon / field distributions.
    """
    folios = semantic_horizon.get("per_folio", [])
    if not folios:
        return {
            "meta": {
                "version": "3.8",
                "description": "Empty horizon map (no folios).",
            },
            "fields": {},
        }

    cont_vals = [f.get("continuity_avg", 0.0) for f in folios]
    press_vals = [f.get("local_theme_pressure", 0.0) for f in folios]
    dens_vals = [f.get("local_motif_density", 0.0) for f in folios]

    def stats(values: List[float]) -> Dict[str, float]:
        if not values:
            return {"min": 0.0, "max": 0.0, "avg": 0.0}
        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / float(len(values)),
        }

    return {
        "meta": {
            "version": "3.8",
            "description": "Global semantic horizon field distributions.",
        },
        "fields": {
            "continuity_avg": stats(cont_vals),
            "theme_pressure": stats(press_vals),
            "motif_density": stats(dens_vals),
        },
    }


def build_horizon_intersections(semantic_horizon: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identify:
      • folios with relatively balanced top themes (implied intersections)
      • clusters that span multiple themes (theme-diverse clusters)
    """
    per_folio = semantic_horizon.get("per_folio", [])
    clusters = semantic_horizon.get("clusters", [])

    # Folio intersections: high continuity but non-extreme dominant_score
    intersect_folios: List[Dict[str, Any]] = []
    for f in per_folio:
        dom_score = _safe_float(f.get("dominant_score"))
        cont = _safe_float(f.get("continuity_avg"))
        # Heuristic: intersections where meaning is strong but not monopolized by one theme
        if cont >= 0.1 and 0.35 <= dom_score <= 0.8:
            intersect_folios.append(
                {
                    "folio_id": f["folio_id"],
                    "dominant_theme": f.get("dominant_theme"),
                    "dominant_score": dom_score,
                    "continuity_avg": cont,
                    "local_theme_pressure": f.get("local_theme_pressure", 0.0),
                }
            )

    # Cluster intersections: clusters with high theme_diversity
    intersect_clusters: List[Dict[str, Any]] = []
    for c in clusters:
        diversity = _safe_int(c.get("theme_diversity"))
        if diversity >= 2:
            intersect_clusters.append(
                {
                    "cluster_id": c.get("cluster_id"),
                    "num_folios": _safe_int(c.get("num_folios")),
                    "theme_diversity": diversity,
                    "themes": c.get("themes", []),
                    "continuity_avg": _safe_float(c.get("continuity_avg")),
                }
            )

    return {
        "meta": {
            "version": "3.8",
            "description": "Intersections where themes and clusters co-occupy meaning space.",
        },
        "folio_intersections": intersect_folios,
        "cluster_intersections": intersect_clusters,
    }


def build_meaning_pressure(semantic_horizon: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a compact pressure scoreboard for themes & clusters.
    """
    per_folio = semantic_horizon.get("per_folio", [])
    themes = semantic_horizon.get("themes", [])
    clusters = semantic_horizon.get("clusters", [])

    # Theme pressure (from theme horizon entries)
    theme_scores: List[Dict[str, Any]] = []
    for t in themes:
        theme_scores.append(
            {
                "theme_label": t.get("theme_label"),
                "num_dominant_folios": _safe_int(t.get("num_dominant_folios")),
                "avg_theme_pressure": _safe_float(t.get("avg_theme_pressure")),
                "avg_continuity": _safe_float(t.get("avg_continuity")),
            }
        )
    theme_scores.sort(key=lambda x: x["avg_theme_pressure"], reverse=True)

    # Cluster pressure: use num_folios * continuity_avg as a simple proxy
    cluster_scores: List[Dict[str, Any]] = []
    for c in clusters:
        nf = _safe_int(c.get("num_folios"))
        ca = _safe_float(c.get("continuity_avg"))
        pressure = nf * ca
        cluster_scores.append(
            {
                "cluster_id": c.get("cluster_id"),
                "num_folios": nf,
                "continuity_avg": ca,
                "theme_diversity": _safe_int(c.get("theme_diversity")),
                "pressure": pressure,
            }
        )
    cluster_scores.sort(key=lambda x: x["pressure"], reverse=True)

    # Folio pressure: rank by local_theme_pressure
    folio_scores: List[Dict[str, Any]] = []
    for f in per_folio:
        folio_scores.append(
            {
                "folio_id": f.get("folio_id"),
                "dominant_theme": f.get("dominant_theme"),
                "local_theme_pressure": _safe_float(f.get("local_theme_pressure")),
                "continuity_avg": _safe_float(f.get("continuity_avg")),
            }
        )
    folio_scores.sort(key=lambda x: x["local_theme_pressure"], reverse=True)

    return {
        "meta": {
            "version": "3.8",
            "description": "Meaning pressure scoreboard across themes, clusters, and folios.",
        },
        "themes": theme_scores,
        "clusters": cluster_scores,
        "folios": folio_scores,
    }


# ────────────────────────────────────────────────────────────────────
# Pipeline
# ────────────────────────────────────────────────────────────────────

def run_v3_8_pipeline() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    atlas_graph = _load_json(ATLAS_GRAPH)
    atlas_summary = _load_json(ATLAS_SUMMARY)
    meaning_index = _load_json(MEANING_INDEX)
    try:
        meaning_flow = _load_json(MEANING_FLOW)
    except FileNotFoundError:
        meaning_flow = {}

    semantic_horizon = build_semantic_horizon(
        atlas_graph=atlas_graph,
        atlas_summary=atlas_summary,
        meaning_flow=meaning_flow,
        meaning_index=meaning_index,
    )
    horizon_map = build_horizon_map(semantic_horizon)
    horizon_intersections = build_horizon_intersections(semantic_horizon)
    meaning_pressure = build_meaning_pressure(semantic_horizon)

    _write_json(SEMANTIC_HORIZON, semantic_horizon)
    _write_json(HORIZON_MAP, horizon_map)
    _write_json(HORIZON_INTERSECTIONS, horizon_intersections)
    _write_json(MEANING_PRESSURE, meaning_pressure)

    # Ledger entry
    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": ts,
        "version": "3.8",
        "num_folios": len(semantic_horizon.get("per_folio", [])),
        "num_themes": len(semantic_horizon.get("themes", [])),
        "num_clusters": len(semantic_horizon.get("clusters", [])),
    }
    _append_ledger_entry(HORIZON_LEDGER, entry)

    print(f"Semantic horizon    → {SEMANTIC_HORIZON}")
    print(f"Horizon map         → {HORIZON_MAP}")
    print(f"Horizon intersections → {HORIZON_INTERSECTIONS}")
    print(f"Meaning pressure    → {MEANING_PRESSURE}")
    print(f"Ledger append       → {HORIZON_LEDGER}")


if __name__ == "__main__":
    run_v3_8_pipeline()
