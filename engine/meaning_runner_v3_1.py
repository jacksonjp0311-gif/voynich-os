"""Voynich OS — Meaning Runner v3.1

Runs the Meaning Engine over every folio (*.txt) in data/corpus
and writes JSON results into data/meaning_v3_1/.

Each output file:
    data/meaning_v3_1/Fxx*.json

This module is deterministic and non-adaptive.
"""

from __future__ import annotations
from pathlib import Path
import json

from .meaning_engine_v3_1 import analyze_line

REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO_ROOT / "data" / "corpus"
OUTPUT_DIR = REPO_ROOT / "data" / "meaning_v3_1"


def _read_folio_lines(folio_path: Path) -> list[str]:
    lines: list[str] = []
    with folio_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)
    return lines


def analyze_folio(folio_path: Path) -> dict:
    lines = _read_folio_lines(folio_path)
    analyses = []
    for idx, line in enumerate(lines):
        result = analyze_line(line)
        analyses.append(
            {
                "line_index": idx,
                "analysis": result,
            }
        )

    return {
        "folio": folio_path.stem,
        "num_lines": len(lines),
        "lines": analyses,
    }


def run_all_folios() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not CORPUS_DIR.exists():
        print(f"[Meaning v3.1] Corpus directory missing: {CORPUS_DIR}")
        return

    folio_files = sorted(CORPUS_DIR.glob("F*.txt"))
    for folio_path in folio_files:
        result = analyze_folio(folio_path)
        out_path = OUTPUT_DIR / f"{folio_path.stem}_meaning_v3_1.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[Meaning v3.1] Saved → {out_path}")


if __name__ == "__main__":
    run_all_folios()
