from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def read_json_text(path: Path) -> str:
    # utf-8-sig tolerates older JSON artifacts that contain a UTF-8 BOM.
    return path.read_text(encoding="utf-8-sig")

def test_required_repo_spine_exists():
    required = [
        "README.md",
        "requirements.txt",
        "data",
        "docs",
        "engine",
        "examples",
        "logs",
        "state",
        "docs/CLAIM_BOUNDARY.md",
        "docs/REPRODUCIBILITY.md",
        "docs/AI_CONTEXT.md",
    ]

    missing = [p for p in required if not (ROOT / p).exists()]
    assert not missing, f"Missing required repo spine items: {missing}"

def test_corpus_folder_has_voynich_material():
    corpus = ROOT / "data" / "corpus"
    assert corpus.exists(), "data/corpus is missing"

    candidates = list(corpus.glob("*.txt")) + list(corpus.glob("*.json"))
    assert candidates, "data/corpus contains no txt/json corpus files"

def test_generated_output_folders_exist():
    expected = [
        ROOT / "data" / "folio_outputs",
        ROOT / "data" / "meaning",
        ROOT / "data" / "ledger",
    ]

    missing = [str(p.relative_to(ROOT)) for p in expected if not p.exists()]
    assert not missing, f"Missing generated output folders: {missing}"

def test_sample_json_outputs_are_valid():
    sample_roots = [
        ROOT / "data" / "folio_outputs",
        ROOT / "data" / "meaning",
        ROOT / "data" / "manuscript_v12_0",
        ROOT / "data" / "hybrid_v1_0",
    ]

    checked = 0
    errors = []

    for folder in sample_roots:
        if not folder.exists():
            continue

        for path in list(folder.rglob("*.json"))[:10]:
            checked += 1
            try:
                json.loads(read_json_text(path))
            except Exception as exc:
                errors.append(f"{path.relative_to(ROOT)}: {exc}")

    assert checked > 0, "No JSON files found to validate"
    assert not errors, "Invalid JSON samples: " + "; ".join(errors)