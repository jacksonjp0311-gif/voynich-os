\"\"\"Voynich OS virtual machine (public-safe stub).

Builds a trivial state-transition graph from tokens,
REL labels, and STATE labels. Graph is represented as
a plain Python dict and has no recursion or learning.
\"\"\"

from typing import List, Dict, Any
from .tokenizer import tokenize
from .parser import parse
from .rel_classifier import classify_rel
from .state_classifier import classify_state

def run_vm(tokens: List[str]) -> Dict[str, Any]:
    \"\"\"Return a simple graph describing token relations.\"\"\"
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

def run_line(text: str) -> Dict[str, Any]:
    \"\"\"Convenience wrapper: tokenize a line, then build a graph.\"\"\"
    tokens = tokenize(text)
    return run_vm(tokens)
