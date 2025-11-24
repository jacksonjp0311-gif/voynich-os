"""
Voynich OS v5.2 — Semantic Bonding Engine
Role: Take fusion sentences from v5.1 and construct a semantic bond graph:
      sentences → bonds → clusters → summary → ledger.

Design:
  • Robust to missing / malformed upstream JSON
  • Uses simple token-overlap similarity between neighboring sentences
  • Emits a stable bonding structure even with partial data
"""

import json
import math
import pathlib
import datetime
from typing import Any, Dict, List, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

FUSION_DIR     = DATA / "meaning_v5_1"
FUSION_SENT    = FUSION_DIR / "fusion_sentences_v5_1.json"
FUSION_CLU     = FUSION_DIR / "fusion_clusters_v5_1.json"
FUSION_MAP     = FUSION_DIR / "fusion_map_v5_1.json"
FUSION_SUMMARY = FUSION_DIR / "fusion_summary_v5_1.json"

OUT_DIR        = DATA / "meaning_v5_2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BONDS_PATH     = OUT_DIR / "semantic_bonds_v5_2.json"
GRAPH_PATH     = OUT_DIR / "bond_graph_v5_2.json"
CLUSTERS_PATH  = OUT_DIR / "bond_clusters_v5_2.json"
SUMMARY_PATH   = OUT_DIR / "bonding_summary_v5_2.json"
LEDGER_PATH    = OUT_DIR / "bonding_ledger_v5_2.jsonl"


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def safe_load_json(path: pathlib.Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        return default
    except Exception:
        return default


def extract_sentences(obj: Any) -> List[str]:
    """
    Try to find a list of sentence strings inside the v5.1 fusion JSON.
    Common cases:
      • {"sentences": [...]} where each entry is a string or dict
      • a bare list of strings
    """
    sentences: List[str] = []

    # Case 1: dict with "sentences"
    if isinstance(obj, dict) and "sentences" in obj:
        raw = obj["sentences"]
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str):
                    sentences.append(item)
                elif isinstance(item, dict):
                    # try fields like "text" or "sentence"
                    text = item.get("text") or item.get("sentence") or ""
                    if isinstance(text, str) and text.strip():
                        sentences.append(text)

    # Case 2: bare list of strings
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, str):
                sentences.append(item)

    # Fallback: nothing
    return sentences


def tokenize(s: str) -> List[str]:
    # very simple tokenization: lowercase + split on whitespace
    return [tok for tok in s.lower().split() if tok]


def overlap_score(a: str, b: str) -> float:
    """
    Compute a basic Jaccard-like overlap between two sentences based on tokens.
    Score in [0,1]. If either side is empty, returns 0.0.
    """
    toks_a = set(tokenize(a))
    toks_b = set(tokenize(b))
    if not toks_a or not toks_b:
        return 0.0
    inter = len(toks_a & toks_b)
    union = len(toks_a | toks_b)
    if union <= 0:
        return 0.0
    return inter / union


def build_bonds(sentences: List[str], threshold: float = 0.15) -> Tuple[List[Dict[str, Any]], Dict[int, List[int]]]:
    """
    Build a simple bond list and adjacency graph between sentences.
    Only bonds between neighbors (i and i+1) with score >= threshold.
    Returns:
      • bonds: list of edges
      • graph: adjacency list {index: [neighbor_indices]}
    """
    bonds: List[Dict[str, Any]] = []
    graph: Dict[int, List[int]] = {}

    n = len(sentences)
    for i in range(n - 1):
        j = i + 1
        s_i = sentences[i]
        s_j = sentences[j]
        score = overlap_score(s_i, s_j)
        if score >= threshold:
            bonds.append({
                "source": i,
                "target": j,
                "score": score,
                "type": "neighbor_overlap",
            })
            if i not in graph:
                graph[i] = []
            if j not in graph:
                graph[j] = []
            graph[i].append(j)
            graph[j].append(i)

    return bonds, graph


def connected_components(graph: Dict[int, List[int]], n_nodes: int) -> List[List[int]]:
    """
    Compute connected components in an undirected graph (0..n_nodes-1).
    Nodes with no edges become singleton components.
    """
    visited = set()
    components: List[List[int]] = []

    for node in range(n_nodes):
        if node in visited:
            continue
        stack = [node]
        comp: List[int] = []
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            comp.append(cur)
            for nb in graph.get(cur, []):
                if nb not in visited:
                    stack.append(nb)
        components.append(sorted(comp))
    return components


# ─────────────────────────────────────────────────────────────
# Core pipeline
# ─────────────────────────────────────────────────────────────

def run():
    timestamp = datetime.datetime.utcnow().isoformat()

    fusion_obj   = safe_load_json(FUSION_SENT, default={})
    clusters_obj = safe_load_json(FUSION_CLU,  default={})
    map_obj      = safe_load_json(FUSION_MAP,  default={})
    summary_obj  = safe_load_json(FUSION_SUMMARY, default={})

    sentences = extract_sentences(fusion_obj)
    num_sentences = len(sentences)

    bonds: List[Dict[str, Any]] = []
    graph: Dict[int, List[int]] = {}
    components: List[List[int]] = []

    if num_sentences > 0:
        bonds, graph = build_bonds(sentences, threshold=0.15)
        components = connected_components(graph, num_sentences)

    num_bonds = len(bonds)
    num_components = len(components)
    max_component_size = max((len(c) for c in components), default=0)

    bonds_obj = {
        "meta": {
            "description": "Semantic bonds between v5.1 fused sentences.",
            "version": "5.2",
            "timestamp": timestamp,
        },
        "sentences_count": num_sentences,
        "bonds_count": num_bonds,
        "bonds": bonds,
    }

    graph_obj = {
        "meta": {
            "description": "Semantic bonding graph (adjacency list) over v5.1 fused sentences.",
            "version": "5.2",
            "timestamp": timestamp,
        },
        "nodes": list(range(num_sentences)),
        "adjacency": graph,
    }

    clusters_obj_v52 = {
        "meta": {
            "description": "Bond-based sentence clusters (connected components).",
            "version": "5.2",
            "timestamp": timestamp,
        },
        "components": components,
    }

    summary = {
        "version": "5.2",
        "timestamp": timestamp,
        "num_sentences": num_sentences,
        "num_bonds": num_bonds,
        "num_components": num_components,
        "max_component_size": max_component_size,
        "notes": "v5.2 Semantic Bonding Engine successfully built a cohesion graph from v5.1 fusion sentences.",
        "upstream": {
            "fusion_summary_present": bool(summary_obj),
            "fusion_clusters_present": bool(clusters_obj),
            "fusion_map_present": bool(map_obj),
        },
    }

    def dump(path: pathlib.Path, obj: Any) -> None:
        path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

    dump(BONDS_PATH, bonds_obj)
    dump(GRAPH_PATH, graph_obj)
    dump(CLUSTERS_PATH, clusters_obj_v52)
    dump(SUMMARY_PATH, summary)

    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(summary) + "\n")

    print("Semantic bonds v5.2       →", BONDS_PATH)
    print("Bond graph v5.2           →", GRAPH_PATH)
    print("Bond clusters v5.2        →", CLUSTERS_PATH)
    print("Bonding summary v5.2      →", SUMMARY_PATH)
    print("Bonding ledger v5.2 append→", LEDGER_PATH)


if __name__ == "__main__":
    run()
