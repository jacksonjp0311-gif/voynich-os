from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "OneDrive" / "Desktop" / "voynich-os"

def write_text(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8-sig")

def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print()
    print("RUN:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, shell=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if check and result.returncode != 0:
        raise SystemExit(f"FAILED: {' '.join(cmd)}")
    return result

def patch_readme() -> None:
    readme_path = ROOT / "README.md"
    text = readme_path.read_text(encoding="utf-8-sig")

    import re

    text = re.sub(
        r"Current checkpoint: \*\*Voynich OS v12\.[^*]+\*\*",
        "Current checkpoint: **Voynich OS v12.5.2 - README Drift Guard and Validation Stop Gate**",
        text,
    )

    text = re.sub(
        r"Previous seal: \*\*Voynich OS v12\.[^*]+\*\*",
        "Previous seal: **Voynich OS v12.5.1 - README Alignment and Roadmap Seal**",
        text,
    )

    lineage_block = """## Release Lineage

| Version | Meaning |
|---|---|
| v12.0 | Existing all-one Voynich OS chain through upstream-to-v12 state. |
| v12.1 | Evidence boundary, reproducibility docs, AI context, audit script, repo spine tests. |
| v12.1.1 | JSON BOM normalization, encoding hygiene, tests repaired and passing. |
| v12.2 | RCC Nexus professional spine, AGENTS contract, context indexes, route map, mini READMEs, checkers. |
| v12.2.1 | Main README Nexus discipline mirror and public operating-memory surface. |
| v12.2.2 | Public README professional replacement with evidence-bounded opening. |
| v12.3 | Output manifest and alias layer: artifact families counted, hashed, bounded, and route-aliased. |
| v12.4 | Showcase evidence package and visual atlas: artifact field made public-demo ready. |
| v12.5 | Reproducibility replay contract: artifact surfaces classified by replay readiness. |
| v12.5.1 | README alignment and roadmap seal: public top-level README synchronized with v12.3-v12.5 evidence stack. |
| v12.5.2 | README drift guard and validation stop gate: failed validation blocks commit/push promotion. |

## Next Recommended Version

Voynich OS v12.6 - Replay Evidence Package

Recommended goals:

- Execute all `replayable_now` contracts from `reports/replay/replay_contract_v12_5.json`.
- Record pass/fail, command, expected property, observed property, and drift status.
- Keep `observed_not_yet_replay_mapped` families visible as repair targets.
- Do not claim full reproducibility until generated families have replay commands.
- Preserve replay-success-is-not-decipherment locks.

"""

    text = re.sub(
        r"## Release Lineage.*?(?=---\s*<!-- VOYNICH_OS_V12_3_OUTPUT_MANIFEST_START -->)",
        lineage_block,
        text,
        flags=re.S,
    )

    roadmap_block = """<!-- VOYNICH_OS_ROADMAP_SEAL_START -->

## Roadmap Seal

| Version | Phase | Proof surface |
|---|---|---|
| v12.2.2 | Claim-boundary stabilization | Public README no longer opens with overclaiming language. |
| v12.3 | Artifact observability | Manifested artifact families, counts, hashes, aliases, and boundaries. |
| v12.4 | Showcase readiness | Public evidence package and visual atlas. |
| v12.5 | Replay classification | Replayable, source-anchored, and observed-not-mapped contract classes. |
| v12.5.1 | README alignment | Public README top-level identity synchronized with the evidence stack. |
| v12.5.2 | Drift guard | README/state drift and failed validation now block promotion. |
| v12.6 | Replay evidence | Execute replayable contracts and report pass/fail evidence. |
| v12.7 | Release candidate | Freeze release notes, visuals, validation logs, and public claim boundary. |
| v12.8 | Corpus provenance cards | Source humility, transcription boundaries, and corpus provenance. |
| v12.9 | Baseline/control layer | Compare outputs against simple controls and ordinary baselines. |
| v13.0 | Research release candidate | Public package: what this proves, what this does not prove, and what remains open. |

Current proof posture:

- v12.5 proves replay readiness classification.
- v12.5 does not prove full replay completion.
- v12.5.1 proves README/evidence-stack alignment.
- v12.5.2 proves failed validation can block commit/push promotion.
- v12.6 is required before claiming replay evidence.

<!-- VOYNICH_OS_ROADMAP_SEAL_END -->"""

    start = "<!-- VOYNICH_OS_ROADMAP_SEAL_START -->"
    end = "<!-- VOYNICH_OS_ROADMAP_SEAL_END -->"
    if start in text:
        text = re.sub(re.escape(start) + r".*?" + re.escape(end), roadmap_block, text, flags=re.S)
    else:
        marker = "<!-- VOYNICH_OS_V12_3_OUTPUT_MANIFEST_START -->"
        if marker in text:
            text = text.replace(marker, roadmap_block + "\n\n---\n\n" + marker)
        else:
            text = text.rstrip() + "\n\n---\n\n" + roadmap_block + "\n"

    readme_path.write_text(text, encoding="utf-8")

def write_readme_audit() -> None:
    code = r'''
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_MARKERS = [
    "Current checkpoint: **Voynich OS v12.5.2 - README Drift Guard and Validation Stop Gate**",
    "Previous seal: **Voynich OS v12.5.1 - README Alignment and Roadmap Seal**",
    "Voynich OS v12.3 - Output Manifest and Alias Layer",
    "Voynich OS v12.4 - Showcase Evidence Package and Visual Atlas",
    "Voynich OS v12.5 - Reproducibility Replay Contract",
    "Voynich OS v12.6 - Replay Evidence Package",
    "Roadmap Seal",
    "v12.5 proves replay readiness classification",
    "v12.5.2 proves failed validation can block commit/push promotion",
    "v12.6 is required before claiming replay evidence",
    "reports/replay/replay_contract_v12_5.json",
    "visuals/replay/v12_5_replay_contract.svg",
    "Modeling is not decipherment",
    "Structure is not translation",
    "Clusters are not meaning",
    "Validation remains required"
]

FORBIDDEN_OVERCLAIMS = [
    "proving the Voynich Manuscript is not a language",
    "first computational proof",
    "The OS has awakened",
    "The manuscript runs",
    "This is the first computational proof",
    "fully-structured proto-operating system"
]

FORBIDDEN_STALE_MARKERS = [
    "Current checkpoint: **Voynich OS v12.2.2 - Public README Professional Replacement**",
    "Next Recommended Version\n\nVoynich OS v12.3 - Output Manifest and Alias Layer"
]

REQUIRED_FILES = [
    "state/manifests/voynich_output_manifest_v12_3.json",
    "releases/showcase_v12_4/showcase_evidence_package_v12_4.json",
    "reports/replay/replay_contract_v12_5.json",
    "reports/replay/replay_contract_v12_5.md",
    "docs/replay/replay_contract_v12_5.md",
    "docs/context/replay_contract_index_v12_5.json",
    "visuals/replay/v12_5_replay_contract.svg",
    "releases/replay_contract_v12_5/README.md",
    "releases/replay_contract_v12_5/replay_contract_v12_5.json",
    "reports/readme/readme_alignment_v12_5_1.json",
    "reports/readme/readme_alignment_v12_5_1.md",
    "scripts/rcc/validate_before_commit.py"
]

def main() -> int:
    readme = ROOT / "README.md"
    errors = []
    warnings = []

    if not readme.exists():
        errors.append("README.md missing")
        text = ""
    else:
        text = readme.read_text(encoding="utf-8-sig")

    for marker in REQUIRED_MARKERS:
        if marker not in text:
            errors.append(f"README missing marker: {marker}")

    for phrase in FORBIDDEN_OVERCLAIMS:
        if phrase in text:
            errors.append(f"README contains forbidden overclaim: {phrase}")

    for marker in FORBIDDEN_STALE_MARKERS:
        if marker in text:
            errors.append(f"README contains stale marker: {marker}")

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            errors.append(f"missing required evidence file: {rel}")

    if "â" in text:
        warnings.append("README may contain mojibake character: â")

    passed = not errors

    report = {
        "schema": "voynich-os-readme-audit-v12.5.2",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
        "required_markers": len(REQUIRED_MARKERS),
        "forbidden_overclaims": len(FORBIDDEN_OVERCLAIMS),
        "forbidden_stale_markers": len(FORBIDDEN_STALE_MARKERS),
        "required_files": len(REQUIRED_FILES)
    }

    out_dir = ROOT / "reports/readme"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "latest_readme_mini_repo_audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    md = [
        "# Voynich OS README / Mini Repo Audit",
        "",
        f"- schema: {report['schema']}",
        f"- passed: {str(passed).lower()}",
        f"- errors: {len(errors)}",
        f"- warnings: {len(warnings)}",
        f"- required_markers: {len(REQUIRED_MARKERS)}",
        f"- forbidden_overclaims_checked: {len(FORBIDDEN_OVERCLAIMS)}",
        f"- forbidden_stale_markers_checked: {len(FORBIDDEN_STALE_MARKERS)}",
        f"- required_files_checked: {len(REQUIRED_FILES)}",
        "",
        "## Errors",
        "",
        *[f"- {e}" for e in errors],
        "",
        "## Warnings",
        "",
        *[f"- {w}" for w in warnings],
        "",
        "## Non-claim lock",
        "",
        "README audits, manifests, showcase packages, replay contracts, alignment seals, and stop gates improve repository observability. They do not prove decipherment, translation, runtime correctness, full reproducibility, or production readiness.",
        "",
    ]

    (out_dir / "latest_readme_mini_repo_audit.md").write_text("\n".join(md), encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(main())
'''
    write_text("scripts/rcc/audit_readme_surface.py", code.strip() + "\n")

def write_validation_gate() -> None:
    code = r'''
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]

COMMANDS = [
    ["python", "scripts/voynich_repo_audit.py"],
    ["python", "scripts/rcc/check_rcc_nexus.py"],
    ["python", "scripts/rcc/audit_readme_surface.py"],
    ["python", "-m", "pytest", "-q"],
]

REQUIRED_JSON_PASSED = [
    ("reports/rcc_nexus/latest_rcc_nexus_check.json", "RCC-N"),
    ("reports/readme/latest_readme_mini_repo_audit.json", "README audit"),
]

def run_command(cmd: list[str]) -> dict:
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, shell=False)
    return {
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "passed": result.returncode == 0,
    }

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def main() -> int:
    errors = []
    command_results = []

    for cmd in COMMANDS:
        result = run_command(cmd)
        command_results.append(result)
        print(result["stdout"], end="")
        if result["stderr"]:
            print(result["stderr"], file=sys.stderr, end="")
        if not result["passed"]:
            errors.append(f"command failed: {result['command']}")

    for rel, label in REQUIRED_JSON_PASSED:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"{label} report missing: {rel}")
            continue
        obj = load_json(path)
        if obj.get("passed") is not True:
            errors.append(f"{label} report did not pass: {rel}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8-sig")

    required_readme_markers = [
        "Current checkpoint: **Voynich OS v12.5.2 - README Drift Guard and Validation Stop Gate**",
        "Previous seal: **Voynich OS v12.5.1 - README Alignment and Roadmap Seal**",
        "v12.5 proves replay readiness classification",
        "v12.5.2 proves failed validation can block commit/push promotion",
        "v12.6 is required before claiming replay evidence",
        "Voynich OS v12.6 - Replay Evidence Package",
    ]

    for marker in required_readme_markers:
        if marker not in readme:
            errors.append(f"README drift marker missing: {marker}")

    forbidden_stale_markers = [
        "Current checkpoint: **Voynich OS v12.2.2 - Public README Professional Replacement**",
        "Next Recommended Version\n\nVoynich OS v12.3 - Output Manifest and Alias Layer",
    ]

    for marker in forbidden_stale_markers:
        if marker in readme:
            errors.append(f"stale README marker still present: {marker}")

    report = {
        "schema": "voynich-os-validation-stop-gate-v12.5.2",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "passed": not errors,
        "errors": errors,
        "commands": command_results,
        "rule": "Commit and push are forbidden unless this gate passes.",
        "claim_boundary": "Validation gates prove repository-governance coherence only, not decipherment, translation, or semantic truth.",
    }

    out_dir = ROOT / "reports/readme"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "validation_stop_gate_v12_5_2.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    md = [
        "# Voynich OS v12.5.2 - Validation Stop Gate",
        "",
        f"- passed: {str(report['passed']).lower()}",
        f"- errors: {len(errors)}",
        "- rule: Commit and push are forbidden unless this gate passes.",
        "",
        "## Errors",
        "",
        *[f"- {e}" for e in errors],
        "",
        "## Command results",
        "",
        "| Command | Return code | Passed |",
        "|---|---:|---|",
        *[f"| `{c['command']}` | {c['returncode']} | {str(c['passed']).lower()} |" for c in command_results],
        "",
        "## Non-claim lock",
        "",
        "Validation gates prove repository-governance coherence only, not decipherment, translation, or semantic truth.",
        "",
    ]

    (out_dir / "validation_stop_gate_v12_5_2.md").write_text("\n".join(md), encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
'''
    write_text("scripts/rcc/validate_before_commit.py", code.strip() + "\n")

def main() -> int:
    if not ROOT.exists():
        raise SystemExit(f"Repo root not found: {ROOT}")

    patch_readme()
    write_readme_audit()
    write_validation_gate()

    run(["python", "scripts/rcc/validate_before_commit.py"], check=True)

    add_paths = [
        "README.md",
        "scripts/rcc/audit_readme_surface.py",
        "scripts/rcc/validate_before_commit.py",
        "scripts/rcc/repair_v12_5_2_stop_gate.py",
        "reports/readme",
        "reports/rcc_nexus",
        "state/audits",
    ]

    run(["git", "add", "--", *add_paths], check=True)

    run(["python", "scripts/rcc/validate_before_commit.py"], check=True)
    run(["git", "add", "--", "reports/readme", "reports/rcc_nexus", "state/audits"], check=True)

    status = run(["git", "status", "--short"], check=True)
    print(status.stdout)

    changed_lines = [
        line for line in status.stdout.splitlines()
        if not line.startswith("?? _repo_dumps/")
    ]

    if changed_lines:
        run(["git", "commit", "-m", "Voynich OS v12.5.2 add README drift guard and validation stop gate"], check=True)
        run(["git", "push", "origin", "main"], check=True)
    else:
        print("No v12.5.2 changes to commit.")

    run(["python", "scripts/rcc/validate_before_commit.py"], check=True)

    run(["git", "log", "-6", "--pretty=oneline"], check=True)
    run(["git", "status", "--short"], check=True)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())