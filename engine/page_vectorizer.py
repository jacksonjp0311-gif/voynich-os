"""
Voynich OS — Page Vectorizer v3.2

Builds per-folio structural vectors from data/corpus folio files
using the public-safe token/REL/STATE classifiers.

Outputs:
    data/meaning_v3_2/folios/Fxx_vector.json
    data/meaning_v3_2/page_vectors_index.json
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Any

from .tokenizer import tokenize
from .rel_classifier import classify_rel
from .state_classifier import classify_state


REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO_ROOT / "data" / "corpus"
MEANING_ROOT = REPO_ROOT / "data" / "meaning_v3_2"
FOLIO_OUT_DIR = MEANING_ROOT / "folios"
INDEX_PATH = MEANING_ROOT / "page_vectors_index.json"


def iter_folio_files() -> List[Path]:
    if not CORPUS_DIR.exists():
        return []
    # Expect files like F1R.txt, F1V.txt, etc.
    return sorted(CORPUS_DIR.glob("F*.txt"))


def build_folio_vector(folio_path: Path) -> Dict[str, Any]:
    folio_name = folio_path.stem

    total_lines = 0
    total_tokens = 0

    rel_counts: Dict[str, int] = {}
    state_counts: Dict[str, int] = {}
    token_length_hist: Dict[int, int] = {}

    with folio_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            total_lines += 1
            tokens = tokenize(line)

            for tok in tokens:
                total_tokens += 1

                tlen = len(tok)
                token_length_hist[tlen] = token_length_hist.get(tlen, 0) + 1

                r = classify_rel(tok)
                s = classify_state(tok)

                if r:
                    rel_counts[r] = rel_counts.get(r, 0) + 1
                if s:
                    state_counts[s] = state_counts.get(s, 0) + 1

    # Normalised frequencies (safe deterministic ratios)
    rel_freq: Dict[str, float] = {}
    state_freq: Dict[str, float] = {}

    if total_tokens > 0:
        for k, v in rel_counts.items():
            rel_freq[k] = v / float(total_tokens)
        for k, v in state_counts.items():
            state_freq[k] = v / float(total_tokens)

    vector: Dict[str, Any] = {
        "folio": folio_name,
        "total_lines": total_lines,
        "total_tokens": total_tokens,
        "rel_counts": rel_counts,
        "state_counts": state_counts,
        "rel_freq": rel_freq,
        "state_freq": state_freq,
        "token_length_hist": token_length_hist,
    }
    return vector


def build_all_page_vectors() -> Dict[str, Dict[str, Any]]:
    FOLIO_OUT_DIR.mkdir(parents=True, exist_ok=True)
    MEANING_ROOT.mkdir(parents=True, exist_ok=True)

    folio_files = iter_folio_files()
    index: Dict[str, Dict[str, Any]] = {}

    for folio_path in folio_files:
        vec = build_folio_vector(folio_path)
        folio_name = vec["folio"]
        index[folio_name] = {
            "total_lines": vec["total_lines"],
            "total_tokens": vec["total_tokens"],
            "rel_freq": vec["rel_freq"],
            "state_freq": vec["state_freq"],
        }

        out_path = FOLIO_OUT_DIR / f"{folio_name}_vector.json"
        out_path.write_text(json.dumps(vec, indent=2), encoding="utf-8")
        print(f"[v3.2] Saved folio vector → {out_path}")

    INDEX_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"[v3.2] Page vector index written → {INDEX_PATH}")
    return index


if __name__ == "__main__":
    build_all_page_vectors()
