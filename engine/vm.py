"""Voynich OS virtual machine (public-safe).

Builds a simple state-transition graph from tokens,
REL labels, and STATE labels. Graph is represented as
a plain Python dict; there is no recursion or learning.
"""

from typing import List, Dict, Any
from .rel_classifier import classify_rel
from .state_classifier import classify_state

def run_vm(tokens: List[str]) -> Dict[str, Any]:
    """Return a basic graph describing token relations."""
    nodes = []
    edges = []

    for idx, t in enumerate(tokens):
        rel = classify_rel(t)
        state = classify_state(t)
        node_id = f"n{idx}"
        nodes.append(
            {
                "id": node_id,
                "token": t,
                "rel": rel,
                "state": state,
            }
        )
        if idx > 0:
            edges.append(
                {
                    "source": f"n{idx-1}",
                    "target": node_id,
                }
            )

    return {
        "nodes": nodes,
        "edges": edges,
    }

