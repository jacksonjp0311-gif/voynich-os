"""Voynich OS — Meaning Continuity Engine v3.6

Safe, deterministic folio-to-folio meaning continuity engine for Voynich OS.

Inputs
------
  • data/meaning_v3_4/master_convergence_v3_4.json
      - global cluster + theme + motif + link structure
  • data/meaning_v3_5/meaning_index_v3_5.json
      - per-folio dominant theme, themes_ranked, motifs_ranked, etc.

Outputs (under data/meaning_v3_6/)
----------------------------------
  • folio_transitions_v3_6.json
       - ordered list of transitions between folios
  • continuity_graph_v3_6.json
       - adjacency-style continuity graph
  • meaning_flow_v3_6.json
       - global flow metrics, hotspots, summary of continuity
  • continuity_ledger_v3_6.jsonl
       - append-only log of v3.6 runs

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
OUTDIR      = REPO_ROOT / "data" / "meaning_v3_6"

MASTER_CONVERGENCE = MEANING_V34 / "master_convergence_v3_4.json"
MEANING_INDEX      = MEANING_V35 / "meaning_index_v3_5.json"

FOLIO_TRANSITIONS  = OUTDIR / "folio_transitions_v3_6.json"
CONTINUITY_GRAPH   = OUTDIR / "continuity_graph_v3_6.json"
MEANING_FLOW       = OUTDIR / "meaning_flow_v3_6.json"
CONTINUITY_LEDGER  = OUTDIR / "continuity_ledger_v3_6.jsonl"


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


def _theme_vector_from_entry(entry: Dict[str, Any]) -> Dict[str, float]:
    """
    Build a simple theme-score vector from a folio summary entry.

    Expects entry["top_themes"] ~ [
      {"theme_label": ..., "score": ..., "count": ...}, ...
    ]
    If that schema is slightly different, we attempt to adapt.
    """
    vec: Dict[str, float] = {}
    top_themes = entry.get("top_themes") or entry.get("themes_ranked") or []
    for t in top_themes:
        # Try several possible keys
        label = t.get("theme_label") or t.get("label")
        if label is None:
            continue
        score = t.get("score")
        if score is None:
            # fallback: use count if present
            count = t.get("count")
            if count is None:
                continue
            score = float(count)
        vec[str(label)] = float(score)
    return vec


def _motif_counts_from_entry(entry: Dict[str, Any]) -> Dict[str, float]:
    """
    Build motif counts map from a folio summary entry.

    Expects entry["top_motifs"] ~ [
      {"motif": ..., "count": ...}, ...
    ] or similar.
    """
    counts: Dict[str, float] = {}
    top_motifs = entry.get("top_motifs") or entry.get("motifs_ranked") or []
    for m in top_motifs:
        name = m.get("motif") or m.get("label")
        if name is None:
            continue
        count = m.get("count")
        if count is None:
            count = 1
        counts[str(name)] = float(count)
    return counts


def _normalized_overlap_score(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """
    Compute a simple overlap score between two non-negative vectors:
      score = sum(min(a_i, b_i)) / max(1, sum(a_i) + sum(b_i))

    Result in [0, ~0.5] but stable and monotonic with overlap.
    """
    if not vec_a and not vec_b:
        return 0.0
    common_keys = set(vec_a.keys()) & set(vec_b.keys())
    overlap = 0.0
    for k in common_keys:
        overlap += min(vec_a[k], vec_b[k])
    total = sum(vec_a.values()) + sum(vec_b.values())
    if total <= 0.0:
        return 0.0
    return overlap / total


def _safe_float(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


# ────────────────────────────────────────────────────────────────────
# Core logic
# ────────────────────────────────────────────────────────────────────

def build_folio_summary_map(meaning_index: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Convert meaning_index_v3_5.json into a map folio_id -> summary entry.
    """
    folios = meaning_index.get("folios") or meaning_index.get("data") or []
    out: Dict[str, Dict[str, Any]] = {}
    for entry in folios:
        fid = str(entry.get("folio_id"))
        out[fid] = entry
    return out


def build_ordered_folio_list(folio_map: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Build a deterministic ordering of folio IDs.

    For simplicity:
      • sort lexicographically by folio_id (e.g., F1R, F1V, F10R, ...)
    """
    return sorted(folio_map.keys())


def compute_folio_transitions(
    folio_order: List[str],
    folio_map: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Compute pairwise transitions between successive folios in the given order.

    For each adjacent pair (A, B) we compute:
      • theme_overlap_score
      • motif_overlap_score
      • continuity_score (weighted combo)
    """
    transitions: List[Dict[str, Any]] = []

    for i in range(len(folio_order) - 1):
        fid_a = folio_order[i]
        fid_b = folio_order[i + 1]

        fa = folio_map[fid_a]
        fb = folio_map[fid_b]

        themes_a = _theme_vector_from_entry(fa)
        themes_b = _theme_vector_from_entry(fb)
        motifs_a = _motif_counts_from_entry(fa)
        motifs_b = _motif_counts_from_entry(fb)

        theme_overlap = _normalized_overlap_score(themes_a, themes_b)
        motif_overlap = _normalized_overlap_score(motifs_a, motifs_b)

        # Weighted continuity score: themes heavier than motifs
        continuity_score = 0.7 * theme_overlap + 0.3 * motif_overlap

        trans: Dict[str, Any] = {
            "from_folio": fid_a,
            "to_folio": fid_b,
            "theme_overlap_score": theme_overlap,
            "motif_overlap_score": motif_overlap,
            "continuity_score": continuity_score,
            "from_dominant_theme": fa.get("dominant_theme"),
            "to_dominant_theme": fb.get("dominant_theme"),
            "from_cross_link_degree": _safe_float(fa.get("cross_link_degree")),
            "to_cross_link_degree": _safe_float(fb.get("cross_link_degree")),
        }
        transitions.append(trans)

    return transitions


def build_continuity_graph(
    folio_order: List[str],
    transitions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build a simple continuity graph:
      • nodes: folios
      • edges: adjacency with continuity scores
    """
    node_map: Dict[str, Dict[str, Any]] = {}
    for fid in folio_order:
        node_map[fid] = {
            "id": fid,
            "type": "folio",
        }

    edges: List[Dict[str, Any]] = []
    for t in transitions:
        edge = {
            "source": t["from_folio"],
            "target": t["to_folio"],
            "continuity_score": t["continuity_score"],
            "theme_overlap_score": t["theme_overlap_score"],
            "motif_overlap_score": t["motif_overlap_score"],
        }
        edges.append(edge)

    return {
        "meta": {
            "version": "3.6",
            "description": "Folio continuity graph (adjacent folios, continuity scores).",
        },
        "nodes": list(node_map.values()),
        "edges": edges,
    }


def build_meaning_flow(
    transitions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build global meaning flow summary:
      • continuity distribution
      • hotspots of low continuity (potential breaks/chapters)
      • highly continuous runs (potential sections)
    """
    if not transitions:
        return {
            "meta": {
                "version": "3.6",
                "description": "Meaning flow summary (no transitions present).",
            },
            "stats": {},
            "hotspots": [],
            "high_continuity_segments": [],
        }

    scores = [t["continuity_score"] for t in transitions]
    n = len(scores)
    avg = sum(scores) / float(n)
    min_score = min(scores)
    max_score = max(scores)

    # Simple thresholding for hotspots and high-continuity segments
    low_threshold = max(0.0, avg * 0.5)
    high_threshold = min(1.0, avg * 1.2)

    hotspots: List[Dict[str, Any]] = []
    for idx, t in enumerate(transitions):
        if t["continuity_score"] <= low_threshold:
            hotspots.append(
                {
                    "index": idx,
                    "from_folio": t["from_folio"],
                    "to_folio": t["to_folio"],
                    "continuity_score": t["continuity_score"],
                }
            )

    # Identify contiguous high-continuity segments
    segments: List[Dict[str, Any]] = []
    current_segment: List[Tuple[int, Dict[str, Any]]] = []

    for idx, t in enumerate(transitions):
        if t["continuity_score"] >= high_threshold:
            current_segment.append((idx, t))
        else:
            if current_segment:
                segments.append(_segment_to_summary(current_segment))
                current_segment = []
    if current_segment:
        segments.append(_segment_to_summary(current_segment))

    stats = {
        "num_transitions": n,
        "continuity_avg": avg,
        "continuity_min": min_score,
        "continuity_max": max_score,
        "low_threshold": low_threshold,
        "high_threshold": high_threshold,
    }

    return {
        "meta": {
            "version": "3.6",
            "description": "Meaning flow statistics + hotspots + high-continuity segments.",
        },
        "stats": stats,
        "hotspots": hotspots,
        "high_continuity_segments": segments,
    }


def _segment_to_summary(segment: List[Tuple[int, Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Collapse a contiguous run of high-continuity transitions into a compact summary.
    """
    indices = [idx for idx, _ in segment]
    transitions = [t for _, t in segment]
    start_idx = min(indices)
    end_idx = max(indices)

    from_folio = transitions[0]["from_folio"]
    to_folio = transitions[-1]["to_folio"]

    scores = [t["continuity_score"] for t in transitions]
    avg_score = sum(scores) / float(len(scores))

    return {
        "start_index": start_idx,
        "end_index": end_idx,
        "from_folio": from_folio,
        "to_folio": to_folio,
        "avg_continuity_score": avg_score,
        "length": len(transitions),
    }


def run_v3_6_pipeline() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    master = _load_json(MASTER_CONVERGENCE)
    meaning_index = _load_json(MEANING_INDEX)

    folio_map = build_folio_summary_map(meaning_index)
    folio_order = build_ordered_folio_list(folio_map)
    transitions = compute_folio_transitions(folio_order, folio_map)
    graph = build_continuity_graph(folio_order, transitions)
    flow = build_meaning_flow(transitions)

    _write_json(FOLIO_TRANSITIONS, {"transitions": transitions})
    _write_json(CONTINUITY_GRAPH, graph)
    _write_json(MEANING_FLOW, flow)

    # Ledger entry
    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": ts,
        "version": "3.6",
        "num_folios": len(folio_order),
        "num_transitions": len(transitions),
        "continuity_avg": flow.get("stats", {}).get("continuity_avg"),
        "continuity_min": flow.get("stats", {}).get("continuity_min"),
        "continuity_max": flow.get("stats", {}).get("continuity_max"),
    }
    _append_ledger_entry(CONTINUITY_LEDGER, entry)

    print(f"Folio transitions → {FOLIO_TRANSITIONS}")
    print(f"Continuity graph  → {CONTINUITY_GRAPH}")
    print(f"Meaning flow      → {MEANING_FLOW}")
    print(f"Ledger append     → {CONTINUITY_LEDGER}")


if __name__ == "__main__":
    run_v3_6_pipeline()
