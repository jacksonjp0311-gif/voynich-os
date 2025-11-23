"""Voynich OS — Meaning Engine v3.1 (public-safe)

This module computes *structural meaning features* for each folio.
Meaning here refers ONLY to measurable, deterministic structures:
    - token count
    - REL distribution
    - STATE distribution
    - graph node count
    - graph edge count

This engine:
    • does not infer linguistic meaning
    • does not learn or adapt
    • does not perform semantic interpretation
"""

from __future__ import annotations
import json
from pathlib import Path

from .tokenizer import tokenize
from .rel_classifier import classify_rel
from .state_classifier import classify_state
from .vm import run_vm

REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO_ROOT / "data" / "corpus"
OUT_DIR = REPO_ROOT / "data" / "meaning_v3_1"

def compute_structural_features(line: str):
    """Return a dictionary of deterministic structural features."""
    tokens = tokenize(line)

    rels = [classify_rel(t) for t in tokens]
    states = [classify_state(t) for t in tokens]

    graph = run_vm(tokens)
    node_count = len(graph.get("nodes", []))
    edge_count = len(graph.get("edges", []))

    return {
        "tokens": len(tokens),
        "rels": {r: rels.count(r) for r in set(rels) if r},
        "states": {s: states.count(s) for s in set(states) if s},
        "graph_nodes": node_count,
        "graph_edges": edge_count,
    }

def process_folio(path: Path):
    """Process one folio → structural meaning JSON."""
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    features = [compute_structural_features(ln) for ln in lines]

    return {
        "folio": path.stem,
        "num_lines": len(lines),
        "features": features,
    }

def run_all():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    folios = sorted(CORPUS_DIR.glob("F*.txt"))
    for fp in folios:
        result = process_folio(fp)
        out_path = OUT_DIR / f"{fp.stem}.json"
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"[Meaning v3.1] Saved → {out_path}")

if __name__ == "__main__":
    run_all()
