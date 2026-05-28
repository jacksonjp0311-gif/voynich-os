from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_MARKERS = [
    "Current checkpoint: **Voynich OS v12.5.1 - README Alignment and Roadmap Seal**",
    "Previous seal: **Voynich OS v12.5 - Reproducibility Replay Contract**",
    "Voynich OS v12.3 - Output Manifest and Alias Layer",
    "Voynich OS v12.4 - Showcase Evidence Package and Visual Atlas",
    "Voynich OS v12.5 - Reproducibility Replay Contract",
    "Voynich OS v12.6 - Replay Evidence Package",
    "Roadmap Seal",
    "v12.5 proves replay readiness classification",
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
    "reports/readme/readme_alignment_v12_5_1.md"
]

def load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))

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

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            errors.append(f"missing required evidence file: {rel}")

    contract_path = ROOT / "reports/replay/replay_contract_v12_5.json"
    if contract_path.exists():
        contract = load_json("reports/replay/replay_contract_v12_5.json")
        if contract.get("schema") != "voynich-os-replay-contract-v12.5":
            errors.append("v12.5 replay contract schema mismatch")
        if contract.get("summary", {}).get("total_contracts", 0) <= 0:
            errors.append("v12.5 replay contract has no contracts")

    alignment_path = ROOT / "reports/readme/readme_alignment_v12_5_1.json"
    if alignment_path.exists():
        alignment = load_json("reports/readme/readme_alignment_v12_5_1.json")
        if alignment.get("schema") != "voynich-os-readme-alignment-v12.5.1":
            errors.append("v12.5.1 README alignment schema mismatch")
        if alignment.get("next_recommended_version") != "Voynich OS v12.6 - Replay Evidence Package":
            errors.append("v12.5.1 next recommended version mismatch")

    if "â" in text:
        warnings.append("README may contain mojibake character: â")

    passed = not errors

    report = {
        "schema": "voynich-os-readme-audit-v12.5.1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
        "required_markers": len(REQUIRED_MARKERS),
        "forbidden_overclaims": len(FORBIDDEN_OVERCLAIMS),
        "required_files": len(REQUIRED_FILES)
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
    md.append(f"- required_files_checked: {len(REQUIRED_FILES)}")
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
    md.append("README audits, manifests, showcase packages, replay contracts, and alignment seals improve repository observability. They do not prove decipherment, translation, runtime correctness, full reproducibility, or production readiness.")
    md.append("")

    (out_dir / "latest_readme_mini_repo_audit.md").write_text(
        "\n".join(md),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(main())