\"\"\"Voynich OS — Folio Runner v1.3

Runs the full Voynich-OS pipeline over every folio:

    folio file (.txt) → tokens → REL/STATE tags → graph JSON

Outputs:
    data/folio_outputs/Fxx*.json

This module is deterministic and non-adaptive.
\"\"\"

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any

from .tokenizer import tokenize
from .vm import run_vm


REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO_ROOT / "data" / "corpus"
OUTPUT_DIR = REPO_ROOT / "data" / "folio_outputs"


def process_folio(folio_path: Path) -> Dict[str, Any]:
    \"\"\"Process a single folio text file into a VM graph structure.\"\"\"
    lines = []
    with folio_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            lines.append(line)

    graphs = []
    for idx, line in enumerate(lines):
        tokens = tokenize(line)
        graph = run_vm(tokens)
        graphs.append(
            {
                "line_index": idx,
                "text": line,
                "graph": graph,
            }
        )

    return {
        "folio": folio_path.stem,
        "num_lines": len(lines),
        "graphs": graphs,
    }


def run_all_folios() -> None:
    \"\"\"Run the pipeline for every folio and save JSON outputs.\"\"\"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    folio_files = sorted(CORPUS_DIR.glob("F*.txt"))
    for folio_path in folio_files:
        result = process_folio(folio_path)
        out_path = OUTPUT_DIR / f"{folio_path.stem}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f\"Saved folio output → {out_path}\")


if __name__ == "__main__":
    run_all_folios()
