from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "README.md",
    "README_90_SECONDS.md",
    "AGENTS.md",
    "docs/CLAIM_BOUNDARY.md",
    "docs/REPRODUCIBILITY.md",
    "docs/AI_CONTEXT.md",
    "docs/context/repository_context_index.json",
    "docs/context/rcc_nexus_index.json",
    "rcc/nexus/README.md",
    "rcc/nexus/route_map.json",
    "rcc/nexus/task_routing_matrix.md",
    "rcc/nexus/rcc_nexus_protocol.md",
    "rcc/nexus/agent_handoff_contract.md"
]

MAJOR_DIRS = [
    "data",
    "docs",
    "engine",
    "examples",
    "export_v4_5",
    "import_v4_5",
    "logs",
    "state",
    "scripts",
    "rcc",
    "reports",
    "artifacts",
    "sources",
    "visuals",
    "tests"
]

LOCK_PHRASES = [
    "Modeling is not decipherment",
    "Structure is not translation",
    "Clusters are not meaning",
    "Validation remains required"
]

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def main() -> int:
    errors = []
    warnings = []

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            errors.append(f"missing required file: {rel}")

    for d in MAJOR_DIRS:
        readme = ROOT / d / "README.md"
        if not readme.exists():
            errors.append(f"missing mini README: {d}/README.md")

    index_path = ROOT / "docs/context/rcc_nexus_index.json"
    if index_path.exists():
        index = load_json(index_path)
        profile = index.get("repository", {}).get("adoption_profile")
        if profile not in {"Lite", "Standard", "Full", "Federated", "Critical"}:
            errors.append(f"invalid RCC-N adoption profile: {profile}")

        locks = index.get("non_claim_locks", {})
        for key in [
            "profile_adoption_is_not_validation",
            "validation_remains_required",
            "modeling_is_not_decipherment",
            "structure_is_not_translation",
            "clusters_are_not_meaning"
        ]:
            if not locks.get(key):
                errors.append(f"missing non-claim lock in RCC index: {key}")

    readme_text = ""
    if (ROOT / "README.md").exists():
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8-sig")

    for phrase in LOCK_PHRASES:
        if phrase not in readme_text:
            warnings.append(f"README missing lock phrase: {phrase}")

    passed = not errors

    report = {
        "schema": "voynich-os-rcc-nexus-check-v12.2",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
        "major_dirs_checked": len(MAJOR_DIRS),
        "mini_readme_coverage": (len(MAJOR_DIRS) - sum(1 for d in MAJOR_DIRS if not (ROOT / d / "README.md").exists())) / len(MAJOR_DIRS),
        "adoption_profile": "Standard",
        "claim_boundary": "RCC-N navigation is not validation; modeling is not decipherment."
    }

    out_dir = ROOT / "reports/rcc_nexus"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "latest_rcc_nexus_check.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    md = []
    md.append("# Voynich OS RCC Nexus Check")
    md.append("")
    md.append(f"- passed: {str(passed).lower()}")
    md.append(f"- errors: {len(errors)}")
    md.append(f"- warnings: {len(warnings)}")
    md.append(f"- major_dirs_checked: {len(MAJOR_DIRS)}")
    md.append(f"- mini_readme_coverage: {report['mini_readme_coverage']}")
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
    md.append("RCC-N navigation is not validation. Modeling is not decipherment.")
    md.append("")

    (out_dir / "latest_rcc_nexus_check.md").write_text(
        "\n".join(md),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(main())