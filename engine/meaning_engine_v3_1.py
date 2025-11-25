"""Voynich OS — Meaning Engine v3.1 (public-safe)

Purpose
-------
Map Voynich EVA lines into structured, inspectable "meaning candidates"
without any adaptive learning or external Codex-style mechanisms.

Inputs (indirect)
-----------------
- engine/tokenizer.py        – split lines into EVA tokens
- engine/rel_classifier.py   – classify relational prefixes (REL)
- engine/state_classifier.py – classify state-like suffixes (STATE)

Outputs
-------
- A per-line dictionary:
    {
      "tokens": [
        {
          "token": "qokeedy",
          "rel": "REL_LINK",      # or None
          "state": "STATE_FLOW",  # or None
          "position": 0,
          "rough_role": "rel+state",
          "notes": "has_rel,has_state"
        },
        ...
      ],
      "pattern": "REL_LINK:STATE_FLOW REL_NONE:STATE_FLOW ...",
      "stats": {...}
    }

This file is deliberately minimal and non-adaptive. It encodes no
hidden protocols, glyph compression, or triadic Codex logic.
"""

from __future__ import annotations
from typing import List, Dict, Any

from pathlib import Path

from .tokenizer import tokenize
from .rel_classifier import classify_rel
from .state_classifier import classify_state


def _rough_role(rel: str | None, state: str | None) -> str:
    """
    Very simple, label-agnostic role tagging based only on the presence
    or absence of REL/STATE classification.
    """
    has_rel = bool(rel)
    has_state = bool(state)

    if has_rel and has_state:
        return "rel+state"
    if has_rel and not has_state:
        return "rel-only"
    if not has_rel and has_state:
        return "state-only"
    return "unclassified"


def _token_notes(rel: str | None, state: str | None) -> str:
    """
    Lightweight descriptor string for debugging / inspection.
    """
    notes: list[str] = []
    if rel:
        notes.append("has_rel")
    else:
        notes.append("no_rel")

    if state:
        notes.append("has_state")
    else:
        notes.append("no_state")

    return ",".join(notes)


def analyze_line(text: str) -> Dict[str, Any]:
    """
    Analyze a single EVA line into a structured representation.
    """
    text = text.strip()
    tokens = tokenize(text)

    annotated: list[dict[str, Any]] = []
    pattern_parts: list[str] = []

    for idx, t in enumerate(tokens):
        rel = classify_rel(t)
        state = classify_state(t)
        role = _rough_role(rel, state)
        notes = _token_notes(rel, state)

        annotated.append(
            {
                "token": t,
                "rel": rel,
                "state": state,
                "position": idx,
                "rough_role": role,
                "notes": notes,
            }
        )

        rel_tag = rel if rel else "REL_NONE"
        state_tag = state if state else "STATE_NONE"
        pattern_parts.append(f"{rel_tag}:{state_tag}")

    pattern = " ".join(pattern_parts)

    stats: dict[str, Any] = {
        "num_tokens": len(tokens),
        "num_rel_labeled": sum(1 for a in annotated if a["rel"]),
        "num_state_labeled": sum(1 for a in annotated if a["state"]),
        "num_rel_and_state": sum(
            1 for a in annotated if a["rel"] and a["state"]
        ),
    }

    return {
        "text": text,
        "tokens": annotated,
        "pattern": pattern,
        "stats": stats,
    }


def analyze_lines(lines: List[str]) -> List[Dict[str, Any]]:
    """
    Convenience function for a batch of lines.
    """
    return [analyze_line(line) for line in lines if line.strip()]


if __name__ == "__main__":
    # Simple CLI: read lines from stdin, emit JSON per line.
    import json
    import sys

    for raw in sys.stdin:
        if not raw.strip():
            continue
        result = analyze_line(raw)
        print(json.dumps(result, ensure_ascii=False))
