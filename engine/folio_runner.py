"""Voynich OS — Folio Runner v1.3

Runs the Voynich-OS pipeline over every folio and produces JSON outputs.
"""
from __future__ import annotations
import json
from pathlib import Path

from .tokenizer import tokenize
from .vm import run_vm

REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO_ROOT / "data" / "corpus"
OUTPUT_DIR = REPO_ROOT / "data" / "folio_outputs"

def process_folio(folio_path: Path):
    lines = []
    with folio_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)

    graphs = []
    for idx, line in enumerate(lines):
        tokens = tokenize(line)
        graph = run_vm(tokens)
        graphs.append({"line_index": idx, "text": line, "graph": graph})

    return {"folio": folio_path.stem, "num_lines": len(lines), "graphs": graphs}

def run_all_folios():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    folios = sorted(CORPUS_DIR.glob("F*.txt"))

    for folio_path in folios:
        result = process_folio(folio_path)
        out_path = OUTPUT_DIR / f"{folio_path.stem}.json"
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Saved folio output → {out_path}")

if __name__ == "__main__":
    run_all_folios()
