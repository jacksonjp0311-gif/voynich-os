\"\"\"Voynich OS — Execution Engine v2.0

Safe, deterministic interpreter mapping EVA tokens to structured objects.
\"\"\"
from __future__ import annotations
from typing import List, Dict, Any

from .tokenizer import tokenize
from .rel_classifier import classify_rel
from .state_classifier import classify_state
from .bnf_grammar import GRAMMAR_RULES
from .transition_graph import build_transition_graph

def interpret_tokens(tokens: List[str]):
    annotated = [
        {"token": t, "rel": classify_rel(t), "state": classify_state(t)}
        for t in tokens
    ]
    graph = build_transition_graph(annotated)
    return {"tokens": annotated, "graph": graph, "grammar_rules": list(GRAMMAR_RULES)}

def interpret_line(text: str):
    return interpret_tokens(tokenize(text))
