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
    "Voynich OS v12.3 - Output Manifest and Alias Layer",
    "Voynich OS v12.4 - Showcase Evidence Package and Visual Atlas",
    "Showcase repository observability, not decipherment",
    "visuals/showcase/v12_4/showcase_evidence_atlas.svg",
    "releases/showcase_v12_4/showcase_evidence_package_v12_4.json",
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
    "reports/output_manifest/latest_output_manifest_v12_3.md",
    "reports/output_manifest/latest_output_manifest_v12_3.json",
    "docs/context/path_aliases_v12_3.json",
    "reports/reorg/path_alias_plan_v12_3.md",
    "reports/showcase/voynich_os_showcase_v12_3.md",
    "visuals/output_manifest/v12_3_output_manifest_layer.svg",
    "releases/showcase_v12_4/README.md",
    "releases/showcase_v12_4/showcase_evidence_package_v12_4.json",
    "reports/showcase/v12_4/latest_showcase_evidence_package_v12_4.md",
    "reports/showcase/v12_4/latest_showcase_evidence_package_v12_4.json",
    "docs/showcase/showcase_atlas_v12_4.md",
    "docs/context/showcase_index_v12_4.json",
    "visuals/showcase/v12_4/showcase_evidence_atlas.svg"
]

def load_json(rel: str):
    path = ROOT / rel
    return json.loads(path.read_text(encoding="utf-8-sig"))

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

    manifest_path = ROOT / "state/manifests/voynich_output_manifest_v12_3.json"
    if manifest_path.exists():
        manifest = load_json("state/manifests/voynich_output_manifest_v12_3.json")
        if manifest.get("schema") != "voynich-os-output-manifest-v12.3":
            errors.append("v12.3 manifest schema mismatch")
        if manifest.get("totals", {}).get("files", 0) <= 0:
            errors.append("v12.3 manifest reports zero files")
        if manifest.get("claim_boundary", {}).get("does_not_prove") is None:
            errors.append("v12.3 manifest missing does_not_prove boundary")

    showcase_path = ROOT / "releases/showcase_v12_4/showcase_evidence_package_v12_4.json"
    if showcase_path.exists():
        showcase = load_json("releases/showcase_v12_4/showcase_evidence_package_v12_4.json")
        if showcase.get("schema") != "voynich-os-showcase-evidence-package-v12.4":
            errors.append("v12.4 showcase package schema mismatch")
        if "does_not_prove" not in showcase:
            errors.append("v12.4 showcase package missing does_not_prove")
        if "public_demonstration_claim" not in showcase:
            errors.append("v12.4 showcase package missing public demonstration claim")

    if "â" in text:
        warnings.append("README may contain mojibake character: â")

    passed = not errors

    report = {
        "schema": "voynich-os-readme-audit-v12.4",
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
    md.append("README audits, output manifests, and showcase packages improve context alignment and artifact observability. They do not prove decipherment, translation, runtime correctness, or production readiness.")
    md.append("")

    (out_dir / "latest_readme_mini_repo_audit.md").write_text(
        "\n".join(md),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(main())