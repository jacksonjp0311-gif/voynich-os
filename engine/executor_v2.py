\"\"\"Voynich OS — Execution Engine v2.0 (safe stub)

Connects:
    * tokenizer
    * REL classifier
    * STATE classifier
    * BNF grammar (structure only)
    * transition graph utilities

This is a safe, non-adaptive interpreter that converts a line of EVA
into a structured representation that can be inspected or visualised.
\"\"\"

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List

from .tokenizer import tokenize
from .rel_classifier import classify_rel
from .state_classifier import classify_state
from .bnf_grammar import GRAMMAR_RULES  # defined in existing module
from .transition_graph import build_transition_graph  # existing helper


def interpret_tokens(tokens: List[str]) -> Dict[str, Any]:
    \"\"\"Return a structured interpretation for a list of tokens.

    This function does not perform any probabilistic inference or
    adaptive learning. It simply applies fixed rules and returns a
    nested dictionary for downstream analysis.
    \"\"\"
    annotated = []
    for t in tokens:
        annotated.append(
            {
                "token": t,
                "rel": classify_rel(t),
                "state": classify_state(t),
            }
        )

    graph = build_transition_graph(annotated)

    return {
        "tokens": annotated,
        "graph": graph,
        "grammar_rules": list(GRAMMAR_RULES.keys()),
    }


def interpret_line(text: str) -> Dict[str, Any]:
    \"\"\"Tokenize and interpret a single line of EVA text.\"\"\"
    tokens = tokenize(text)
    return interpret_tokens(tokens)
