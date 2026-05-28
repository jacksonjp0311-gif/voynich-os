from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_MARKERS = [
    "Voynich OS v12.2.2 - Public README Professional Replacement",
    "Evidence-Bounded Symbolic Manuscript Runtime",
    "Current Research Snapshot",
    "Human Director Box",
    "PART I - Human README",
    "PART II - RCC Nexus README",
    "PART III - AI Agent README",
    "README + Mini Repo Audit Map",
    "AI Failure Learning Ledger",
    "Process Alignment Layer",
    "Full Directory Box",
    "Unified Validation Layer",
    "Public Non-Claim Locks",
    "Release Lineage",
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

    if "â" in text:
        warnings.append("README may contain mojibake character: â")

    passed = not errors

    report = {
        "schema": "voynich-os-readme-audit-v12.2.2",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
        "required_markers": len(REQUIRED_MARKERS),
        "forbidden_overclaims": len(FORBIDDEN_OVERCLAIMS),
    }

    out_dir = ROOT / "reports/readme"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "latest_readme_mini_repo_audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    md = []
    md.append("# Voynich OS README / Mini Repo Audit")
    md.append("")
    md.append(f"- schema: {report['schema']}")
    md.append(f"- passed: {str(passed).lower()}")
    md.append(f"- errors: {len(errors)}")
    md.append(f"- warnings: {len(warnings)}")
    md.append(f"- required_markers: {len(REQUIRED_MARKERS)}")
    md.append(f"- forbidden_overclaims_checked: {len(FORBIDDEN_OVERCLAIMS)}")
    md.append("")
    md.append("## Errors")
    md.append("")
    for e in errors:
        md.append(f"- {e}")
    md.append("")
    md.append("## Warnings")
    md.append("")
    for w in warnings:
        md.append(f"- {w}")
    md.append("")
    md.append("## Non-claim lock")
    md.append("")
    md.append("README audits and mini repo audits improve context alignment. They do not prove decipherment, translation, runtime correctness, or production readiness.")
    md.append("")

    (out_dir / "latest_readme_mini_repo_audit.md").write_text(
        "\n".join(md),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(main())