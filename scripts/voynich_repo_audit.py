from __future__ import annotations

import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def count_files(path: Path, pattern: str = "*") -> int:
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob(pattern) if p.is_file())

def main() -> int:
    corpus = ROOT / "data" / "corpus"
    folio_outputs = ROOT / "data" / "folio_outputs"
    meaning = ROOT / "data" / "meaning"
    ledger = ROOT / "data" / "ledger"
    docs = ROOT / "docs"
    ivtff = corpus / "voynich_corpus_ivtff.txt"

    report = {
        "artifact": "Voynich OS repo audit",
        "version": "v12.1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(ROOT),
        "claim_boundary": "Modeling is not decipherment; structure is not translation; clusters are diagnostics, not literal meaning.",
        "counts": {
            "corpus_txt_files": count_files(corpus, "*.txt"),
            "corpus_json_files": count_files(corpus, "*.json"),
            "folio_output_json_files": count_files(folio_outputs, "*.json"),
            "meaning_json_files": count_files(meaning, "*.json"),
            "ledger_jsonl_files": count_files(ledger, "*.jsonl"),
            "docs_md_files": count_files(docs, "*.md"),
        },
        "hashes": {},
        "required_docs": {
            "CLAIM_BOUNDARY.md": (docs / "CLAIM_BOUNDARY.md").exists(),
            "REPRODUCIBILITY.md": (docs / "REPRODUCIBILITY.md").exists(),
            "AI_CONTEXT.md": (docs / "AI_CONTEXT.md").exists(),
        },
    }

    if ivtff.exists():
        report["hashes"]["data/corpus/voynich_corpus_ivtff.txt"] = sha256_file(ivtff)

    out_dir = ROOT / "state" / "audits"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "voynich_repo_audit_v12_1.json"
    out_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("")
    print(f"Wrote: {out_file.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())