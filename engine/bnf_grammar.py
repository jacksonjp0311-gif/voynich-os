"""Voynich OS BNF-style grammar (public-safe stub).

This module exposes a simple BNF-like representation of
a process language for Voynich lines. It DOES NOT claim
to be the true underlying grammar of the manuscript; it
serves as a working hypothesis and a convenient formalism
for experimentation.
"""

from typing import Dict, List

# Grammar is represented as:
#   nonterminal -> list of productions
#   each production is a list of symbols (strings)
#
# Terminals here are abstract categories like REL, STEM, STATE.

GRAMMAR: Dict[str, List[List[str]]] = {
    "LINE": [
        ["PHRASE"],
        ["PHRASE", "LINE"],
    ],
    "PHRASE": [
        ["WORD"],
        ["WORD", "WORD"],
    ],
    "WORD": [
        ["REL", "STEM", "STATE"],
        ["REL", "STEM"],
        ["STEM", "STATE"],
        ["STEM"],
    ],
    "REL": [
        ["REL_Q"],
        ["REL_QO"],
        ["REL_OL"],
        ["REL_OR"],
        ["REL_AL"],
    ],
    "STATE": [
        ["STATE_Y"],
        ["STATE_DY"],
        ["STATE_AIN"],
        ["STATE_AIIN"],
        ["STATE_CHEDY"],
    ],
}

def get_grammar() -> Dict[str, List[List[str]]]:
    """Return the current BNF-style grammar hypothesis."""
    return GRAMMAR

