\"\"\"Voynich OS — Corpus Statistics v1.2

Safe, deterministic corpus validators for the Voynich-OS project.

Functions:
    * scan_corpus()      – iterate over all folio files under data/corpus
    * compute_statistics – token, REL, STATE, and line length frequencies
    * write_json_report  – save stats to data/corpus/corpus_stats.json

This module does not learn or adapt. All behaviour is rule-based.
\"\"\"

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Tuple

from .tokenizer import tokenize
from .rel_classifier import classify_rel
from .state_classifier import classify_state


REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO_ROOT / "data" / "corpus"
STATS_PATH = CORPUS_DIR / "corpus_stats.json"


def iter_folio_files() -> List[Path]:
    \"\"\"Return all folio .txt files under data/corpus sorted by name.\"\"\"
    if not CORPUS_DIR.exists():
        return []
    return sorted(CORPUS_DIR.glob("F*.txt"))


def scan_corpus() -> Dict:
    \"\"\"Scan every folio file and accumulate basic statistics.\"\"\"
    folios = iter_folio_files()

    total_lines = 0
    total_tokens = 0

    rel_counts: Dict[str, int] = {}
    state_counts: Dict[str, int] = {}
    token_length_hist: Dict[int, int] = {}
    line_length_hist: Dict[int, int] = {}

    per_folio: Dict[str, Dict[str, int]] = {}

    for folio_path in folios:
        folio_name = folio_path.stem
        f_lines = 0
        f_tokens = 0

        with folio_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                f_lines += 1
                total_lines += 1

                tokens = tokenize(line)
                length = len(tokens)
                line_length_hist[length] = line_length_hist.get(length, 0) + 1

                for tok in tokens:
                    f_tokens += 1
                    total_tokens += 1

                    # token length histogram
                    tlen = len(tok)
                    token_length_hist[tlen] = token_length_hist.get(tlen, 0) + 1

                    # REL & STATE classification
                    r = classify_rel(tok)
                    s = classify_state(tok)

                    if r is not None:
                        rel_counts[r] = rel_counts.get(r, 0) + 1
                    if s is not None:
                        state_counts[s] = state_counts.get(s, 0) + 1

        per_folio[folio_name] = {
            "lines": f_lines,
            "tokens": f_tokens,
        }

    return {
        "total_folios": len(folios),
        "total_lines": total_lines,
        "total_tokens": total_tokens,
        "rel_counts": rel_counts,
        "state_counts": state_counts,
        "token_length_hist": token_length_hist,
        "line_length_hist": line_length_hist,
        "per_folio": per_folio,
    }


def write_json_report(path: Path | None = None) -> Path:
    \"\"\"Compute statistics and write them as JSON to *path*.\"\"\"
    if path is None:
        path = STATS_PATH

    stats = scan_corpus()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, sort_keys=True)
    return path


if __name__ == "__main__":
    out = write_json_report()
    print(f\"Corpus statistics written to: {out}\")
