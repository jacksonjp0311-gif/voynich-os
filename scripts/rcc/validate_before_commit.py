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
