$ErrorActionPreference = "Stop"

$RepoRoot = Join-Path $env:USERPROFILE "OneDrive\Desktop\voynich-os"
Set-Location $RepoRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "════════════════════════════════════════════════════════════"
    Write-Host " $Message"
    Write-Host "════════════════════════════════════════════════════════════"
}

function Write-Utf8 {
    param(
        [string]$Path,
        [AllowEmptyString()][string]$Content = ""
    )
    $Parent = Split-Path -Parent $Path
    if (-not (Test-Path $Parent)) {
        New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

Write-Step "Voynich OS v12.1 Governance Patch"

if (Test-Path ".git\index.lock") {
    Remove-Item ".git\index.lock" -Force
}

New-Item -ItemType Directory -Force -Path "docs","tests","scripts","state\audits" | Out-Null

$ClaimBoundary = @"
# Voynich OS — Claim Boundary

## Purpose

Voynich OS is a computational modeling framework for representing Voynich Manuscript transcription structures as symbolic graph, state, process, and clustering artifacts.

It is designed to support reproducible structural analysis of the corpus.

## What this project may claim

Voynich OS may claim that it:

- parses available Voynich transcription data into local computational artifacts;
- emits folio-level graph/state JSON outputs;
- builds diagnostic feature, meaning-vector, cluster, and manuscript-level summaries;
- preserves generated outputs in data, state, logs, and ledger folders;
- provides an experimental substrate for testing symbolic-process interpretations of the manuscript.

## What this project must not claim

Voynich OS must not claim that it:

- proves the Voynich Manuscript is an operating system;
- proves a decipherment;
- proves semantic translation;
- proves authorial intent;
- proves biological, astronomical, botanical, ritual, or computational meaning;
- treats clusters as translations;
- treats meaning vectors as literal meaning;
- treats recurrence as proof of language, code, ritual, or system identity.

## Correct interpretation

Voynich OS tests whether Voynich transcription structures can be modeled as symbolic graph/state/process systems and whether those models emit stable, inspectable, reproducible diagnostic artifacts.

## Evidence classes

- Corpus evidence: transcription files and corpus statistics.
- Structural evidence: parsed folio and graph outputs.
- Diagnostic evidence: feature vectors, clusters, state files, ledgers, and summaries.
- Interpretive hypothesis: any claim about what those structures mean.

Only the first three are computational artifacts. The fourth remains hypothesis.

## Downgrade rule

If a generated structure is unstable, non-reproducible, or baseline-equivalent, it must be downgraded to a diagnostic curiosity rather than treated as evidence for interpretation.

## Canonical lock

Modeling is not decipherment.

Structure is not translation.

Recurrence is not proof.

Clusters are not meaning.

Voynich OS is an experimental evidence-bound analysis substrate, not a solved reading of the manuscript.
"@

Write-Utf8 -Path "docs\CLAIM_BOUNDARY.md" -Content $ClaimBoundary

$Repro = @"
# Voynich OS — Reproducibility Notes

## Purpose

This document defines the minimum reproducibility boundary for Voynich OS outputs.

A generated output should be treated as evidence only when its source corpus, engine version, command path, and output location are clear.

## Required artifact metadata

Every generated layer should ideally preserve:

- input corpus path;
- input corpus hash when possible;
- engine script or module used;
- engine version or repo commit;
- command used;
- timestamp;
- output folder;
- output count;
- summary metrics;
- known limitations;
- claim boundary.

## Current output families

Known output families include:

- data/corpus/
- data/folio_outputs/
- data/meaning/meaning_v3_1/
- data/meaning/meaning_v3_2/
- data/hybrid_v1_0/
- data/manuscript_v12_0/
- data/fields_v11/
- data/ledger/
- logs/
- state/

## Reproducibility standard

An output is considered reproducible when a clean checkout can regenerate it from documented commands without manual hidden state.

## Evidence limitation

Existing checked-in outputs are useful as artifacts, but they should not be treated as validated evidence unless their regeneration path is documented and repeatable.

## Recommended next step

Add a single command or script that regenerates the core pipeline.

Current audit command:

    python scripts/voynich_repo_audit.py
"@

Write-Utf8 -Path "docs\REPRODUCIBILITY.md" -Content $Repro

$AIContext = @"
# Voynich OS — AI Context / RCC Section

## Project identity

Voynich OS is an experimental symbolic-analysis repository for the Voynich Manuscript transcription corpus.

The project models folios as computational artifacts: text lines, tokens, graph nodes, relation/state objects, vectors, clusters, ledgers, and manuscript-level summaries.

## Safe summary for AI agents

This repository provides a reproducible substrate for modeling Voynich transcription structures as symbolic graph/state/process artifacts. It does not prove decipherment or literal operating-system identity.

## Navigation map

- README.md — human-facing overview.
- docs/CLAIM_BOUNDARY.md — claim limits and non-decipherment locks.
- docs/REPRODUCIBILITY.md — reproducibility standard.
- docs/AI_CONTEXT.md — AI/RCC context.
- data/corpus/ — source transcription corpus and folio text files.
- data/folio_outputs/ — generated per-folio graph/state outputs.
- data/meaning/ — generated feature/vector/cluster layers.
- data/ledger/ — run and upstream ledger records.
- engine/ — core processing scripts.
- state/ — state files and run summaries.
- logs/ — logs.
- examples/ — examples.

## AI editing rules

- Do not strengthen claims.
- Do not call clusters translations.
- Do not call meaning vectors literal meanings.
- Do not claim the manuscript is solved.
- Preserve source/provenance boundaries.
- Prefer tests, manifests, audit scripts, and documentation over speculative interpretation.
- Any new theory layer must include a falsification or downgrade path.

## Good next edits

- Add tests for repo spine and JSON validity.
- Add output manifests.
- Add corpus hash reporting.
- Add a regenerate/audit command.
- Add baseline comparisons for clustering or graph metrics.
"@

Write-Utf8 -Path "docs\AI_CONTEXT.md" -Content $AIContext

$TestRepoSpine = @"
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

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
                json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"{path.relative_to(ROOT)}: {exc}")

    assert checked > 0, "No JSON files found to validate"
    assert not errors, "Invalid JSON samples: " + "; ".join(errors)
"@

Write-Utf8 -Path "tests\test_repo_spine.py" -Content $TestRepoSpine

$AuditScript = @"
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
"@

Write-Utf8 -Path "scripts\voynich_repo_audit.py" -Content $AuditScript

Write-Step "Patching README"

$ReadmePath = "README.md"
$Readme = Get-Content -LiteralPath $ReadmePath -Raw -Encoding UTF8
$Marker = "<!-- VOYNICH_OS_V12_1_GOVERNANCE_PATCH -->"

$Patch = @"

---

<!-- VOYNICH_OS_V12_1_GOVERNANCE_PATCH -->

## Voynich OS v12.1 — Evidence Boundary and AI Context

Voynich OS should be interpreted as an experimental symbolic-analysis framework for the Voynich Manuscript transcription corpus.

The repository models Voynich transcription structures as computational artifacts: folio lines, tokens, graph nodes, relation/state objects, feature vectors, clusters, ledgers, and manuscript-level summaries.

### Claim boundary

Voynich OS does **not** prove that the Voynich Manuscript is an operating system.

Voynich OS does **not** prove decipherment.

Voynich OS does **not** prove translation.

Voynich OS does **not** prove authorial intent.

The safe claim is:

Voynich OS tests whether Voynich transcription structures can be represented as symbolic graph/state/process systems and whether those models emit stable, inspectable, reproducible diagnostic artifacts.

### Interpretation locks

- Modeling is not decipherment.
- Structure is not translation.
- Recurrence is not proof.
- Clusters are not literal meanings.
- Meaning vectors are structural diagnostics, not validated semantic readings.
- Generated outputs require reproducibility metadata before being treated as evidence.

### RCC / AI navigation

For AI agents and human reviewers:

- Read docs/CLAIM_BOUNDARY.md before strengthening any claim.
- Read docs/REPRODUCIBILITY.md before treating outputs as evidence.
- Read docs/AI_CONTEXT.md before making automated edits.
- Prefer tests, manifests, audit scripts, and provenance over speculative interpretation.

### v12.1 audit command

    python scripts/voynich_repo_audit.py

Optional test command:

    python -m pytest -q
"@

if ($Readme -notlike "*$Marker*") {
    Add-Content -LiteralPath $ReadmePath -Value $Patch -Encoding UTF8
    Write-Host "README patched."
}

if ($Readme -like "*$Marker*") {
    Write-Host "README already contains v12.1 governance patch."
}

Write-Step "Running audit"

python scripts\voynich_repo_audit.py

Write-Step "Running tests if pytest exists"

$PytestAvailable = $false
try {
    python -m pytest --version | Out-Null
    $PytestAvailable = $true
}
catch {
    $PytestAvailable = $false
}

if ($PytestAvailable -eq $true) {
    python -m pytest -q
}

if ($PytestAvailable -ne $true) {
    Write-Host "pytest not installed. Skipping tests."
}

Write-Step "Git commit and push"

git add README.md docs tests scripts state/audits

$Changes = git status --short

Write-Host $Changes

$FilteredChanges = $Changes | Where-Object { $_ -notmatch "^\?\? _repo_dumps/" }

if ($FilteredChanges) {
    git commit -m "Voynich OS v12.1 evidence boundary and reproducibility patch"
    git push origin main
}

if (-not $FilteredChanges) {
    Write-Host "No patch changes to commit."
}

Write-Step "Final status"

git remote -v
git branch --show-current
git log -1 --pretty=oneline
git status --short

Write-Step "Done"