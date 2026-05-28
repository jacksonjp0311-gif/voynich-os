from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

MANIFEST = ROOT / "state/manifests/voynich_output_manifest_v12_3.json"
SHOWCASE = ROOT / "releases/showcase_v12_4/showcase_evidence_package_v12_4.json"

CLAIM_LOCKS = [
    "Replay classification is not decipherment.",
    "Replay success is not translation.",
    "Hash stability is not semantic truth.",
    "Observed artifacts are not automatically reproducible artifacts.",
    "A missing replay command is a repair target, not a failure of the whole repository.",
    "Validation remains required."
]

CONTRACTS = [
    {
        "contract_id": "source_corpus_hash",
        "surface": "data/corpus/voynich_corpus_ivtff.txt",
        "classification": "source_anchored_verify_hash",
        "command": "python scripts/voynich_repo_audit.py",
        "expected_output": "state/audits/voynich_repo_audit_v12_1.json",
        "expected_property": "hashes.data/corpus/voynich_corpus_ivtff.txt",
        "expected_value": "3f3f2af18cde10efe75c582f49b07b651c3397022fcbfa5854fecc424c121afa",
        "claim_boundary": "Corpus hash verification proves source stability only, not decipherment."
    },
    {
        "contract_id": "repo_audit_replay",
        "surface": "state/audits/voynich_repo_audit_v12_1.json",
        "classification": "replayable_now",
        "command": "python scripts/voynich_repo_audit.py",
        "expected_output": "state/audits/voynich_repo_audit_v12_1.json",
        "expected_property": "artifact",
        "expected_value": "Voynich OS repo audit",
        "claim_boundary": "Repo audit replay proves observable repo counts and required docs only."
    },
    {
        "contract_id": "rcc_nexus_replay",
        "surface": "reports/rcc_nexus/latest_rcc_nexus_check.json",
        "classification": "replayable_now",
        "command": "python scripts/rcc/check_rcc_nexus.py",
        "expected_output": "reports/rcc_nexus/latest_rcc_nexus_check.json",
        "expected_property": "passed",
        "expected_value": True,
        "claim_boundary": "RCC-N replay proves navigation-surface validity only."
    },
    {
        "contract_id": "readme_audit_replay",
        "surface": "reports/readme/latest_readme_mini_repo_audit.json",
        "classification": "replayable_now",
        "command": "python scripts/rcc/audit_readme_surface.py",
        "expected_output": "reports/readme/latest_readme_mini_repo_audit.json",
        "expected_property": "passed",
        "expected_value": True,
        "claim_boundary": "README audit replay proves public framing checks only."
    },
    {
        "contract_id": "output_manifest_replay",
        "surface": "state/manifests/voynich_output_manifest_v12_3.json",
        "classification": "replayable_now",
        "command": "python scripts/manifests/generate_output_manifest_v12_3.py",
        "expected_output": "state/manifests/voynich_output_manifest_v12_3.json",
        "expected_property": "schema",
        "expected_value": "voynich-os-output-manifest-v12.3",
        "claim_boundary": "Manifest replay proves artifact observability only."
    },
    {
        "contract_id": "showcase_package_replay",
        "surface": "releases/showcase_v12_4/showcase_evidence_package_v12_4.json",
        "classification": "replayable_now",
        "command": "python scripts/showcase/build_showcase_package_v12_4.py",
        "expected_output": "releases/showcase_v12_4/showcase_evidence_package_v12_4.json",
        "expected_property": "schema",
        "expected_value": "voynich-os-showcase-evidence-package-v12.4",
        "claim_boundary": "Showcase replay proves package regeneration only."
    },
    {
        "contract_id": "folio_outputs_family",
        "surface": "data/folio_outputs/",
        "classification": "observed_not_yet_replay_mapped",
        "command": None,
        "expected_output": "data/folio_outputs/",
        "expected_property": "file_count",
        "expected_value": 226,
        "claim_boundary": "Observed folio outputs are manifested but not yet replay-command mapped."
    },
    {
        "contract_id": "meaning_vectors_family",
        "surface": "data/meaning/",
        "classification": "observed_not_yet_replay_mapped",
        "command": None,
        "expected_output": "data/meaning/",
        "expected_property": "file_count",
        "expected_value": 546,
        "claim_boundary": "Observed meaning/vector diagnostics are manifested but not yet replay-command mapped."
    },
    {
        "contract_id": "manuscript_state_family",
        "surface": "data/manuscript_v12_0/",
        "classification": "observed_not_yet_replay_mapped",
        "command": None,
        "expected_output": "data/manuscript_v12_0/",
        "expected_property": "file_count",
        "expected_value": 1,
        "claim_boundary": "Observed manuscript state is manifested but not yet replay-command mapped."
    }
]

def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def nested_get(obj: Any, dotted: str) -> Any:
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur

def count_contracts(contracts: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for c in contracts:
        key = c["classification"]
        counts[key] = counts.get(key, 0) + 1
    return counts

def build_svg(summary: dict[str, Any]) -> str:
    replayable = summary["classification_counts"].get("replayable_now", 0)
    source = summary["classification_counts"].get("source_anchored_verify_hash", 0)
    observed = summary["classification_counts"].get("observed_not_yet_replay_mapped", 0)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="520" viewBox="0 0 1200 520">
  <rect width="1200" height="520" fill="#ffffff"/>
  <text x="60" y="60" font-family="Arial" font-size="30" font-weight="bold">Voynich OS v12.5 Replay Contract</text>
  <text x="60" y="100" font-family="Arial" font-size="17">Classifying artifact surfaces by replay readiness.</text>

  <rect x="80" y="155" width="280" height="150" rx="18" fill="#f2f2f2" stroke="#222"/>
  <text x="115" y="205" font-family="Arial" font-size="24" font-weight="bold">{replayable}</text>
  <text x="115" y="245" font-family="Arial" font-size="18">Replayable now</text>

  <rect x="460" y="155" width="280" height="150" rx="18" fill="#f2f2f2" stroke="#222"/>
  <text x="495" y="205" font-family="Arial" font-size="24" font-weight="bold">{source}</text>
  <text x="495" y="245" font-family="Arial" font-size="18">Source anchored</text>

  <rect x="840" y="155" width="280" height="150" rx="18" fill="#f2f2f2" stroke="#222"/>
  <text x="875" y="205" font-family="Arial" font-size="24" font-weight="bold">{observed}</text>
  <text x="875" y="245" font-family="Arial" font-size="18">Observed, not mapped</text>

  <text x="60" y="390" font-family="Arial" font-size="18">Next proof move: turn observed_not_yet_replay_mapped families into replayable_now contracts.</text>
  <text x="60" y="440" font-family="Arial" font-size="15">Non-claim lock: replayability proves process regeneration, not decipherment, translation, or semantic truth.</text>
</svg>
'''

def main() -> int:
    if not MANIFEST.exists():
        raise SystemExit(f"Missing v12.3 manifest: {MANIFEST}")

    if not SHOWCASE.exists():
        raise SystemExit(f"Missing v12.4 showcase package: {SHOWCASE}")

    manifest = read_json(MANIFEST)
    showcase = read_json(SHOWCASE)

    family_counts = {}
    for f in manifest.get("families", []):
        family_counts[f["family_id"]] = f.get("file_count", 0)

    contracts = []
    for c in CONTRACTS:
        item = dict(c)
        item["status"] = "declared"
        if item["classification"] == "observed_not_yet_replay_mapped":
            item["repair_target"] = "Add or recover generator command and expected replay tolerance."
        else:
            item["repair_target"] = None
        contracts.append(item)

    summary = {
        "total_contracts": len(contracts),
        "classification_counts": count_contracts(contracts),
        "replayable_contracts": sum(1 for c in contracts if c["classification"] == "replayable_now"),
        "observed_not_yet_replay_mapped": sum(1 for c in contracts if c["classification"] == "observed_not_yet_replay_mapped")
    }

    package = {
        "schema": "voynich-os-replay-contract-v12.5",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "checkpoint": "Voynich OS v12.5 - Reproducibility Replay Contract",
        "source_manifest": "state/manifests/voynich_output_manifest_v12_3.json",
        "source_showcase_package": "releases/showcase_v12_4/showcase_evidence_package_v12_4.json",
        "purpose": "Classify artifact surfaces by replay readiness before claiming reproducibility.",
        "summary": summary,
        "contracts": contracts,
        "claim_locks": CLAIM_LOCKS,
        "next_layer": {
            "recommended": "Voynich OS v12.6 - Replay Evidence Package",
            "reason": "After declaring replay contracts, run the replayable contracts and record pass/fail evidence, drift, and repair targets."
        }
    }

    write_json(ROOT / "reports/replay/replay_contract_v12_5.json", package)
    write_json(ROOT / "releases/replay_contract_v12_5/replay_contract_v12_5.json", package)
    write_json(ROOT / "docs/context/replay_contract_index_v12_5.json", {
        "schema": "voynich-os-replay-contract-index-v12.5",
        "timestamp_utc": package["timestamp_utc"],
        "contract_file": "reports/replay/replay_contract_v12_5.json",
        "release_contract_file": "releases/replay_contract_v12_5/replay_contract_v12_5.json",
        "visual": "visuals/replay/v12_5_replay_contract.svg",
        "claim_boundary": "Replay contracts classify reproducibility readiness only."
    })

    md = []
    md.append("# Voynich OS v12.5 - Reproducibility Replay Contract")
    md.append("")
    md.append("## Purpose")
    md.append("")
    md.append("v12.5 answers the next proof question: which artifacts can be regenerated now, which are source-anchored, and which are observed but not replay-command mapped yet?")
    md.append("")
    md.append("## Why this matters")
    md.append("")
    md.append("v12.3 made the artifact field measurable. v12.4 made it showable. v12.5 makes it replay-classified.")
    md.append("")
    md.append("## Summary")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|---|---:|")
    md.append(f"| Total replay contracts | {summary['total_contracts']} |")
    md.append(f"| Replayable now | {summary['classification_counts'].get('replayable_now', 0)} |")
    md.append(f"| Source anchored / verify hash | {summary['classification_counts'].get('source_anchored_verify_hash', 0)} |")
    md.append(f"| Observed but not replay mapped | {summary['classification_counts'].get('observed_not_yet_replay_mapped', 0)} |")
    md.append("")
    md.append("## Contracts")
    md.append("")
    md.append("| Contract | Surface | Classification | Command | Boundary |")
    md.append("|---|---|---|---|---|")
    for c in contracts:
        command = c["command"] if c["command"] else "not yet mapped"
        md.append(f"| `{c['contract_id']}` | `{c['surface']}` | {c['classification']} | `{command}` | {c['claim_boundary']} |")
    md.append("")
    md.append("## Claim locks")
    md.append("")
    for lock in CLAIM_LOCKS:
        md.append(f"- {lock}")
    md.append("")
    md.append("## Next layer")
    md.append("")
    md.append("Voynich OS v12.6 - Replay Evidence Package")
    md.append("")
    md.append("Recommended purpose: execute the replayable contracts, capture pass/fail evidence, and convert unmapped generated families into replayable contracts where possible.")
    md.append("")

    text = "\n".join(md)
    write_text(ROOT / "reports/replay/replay_contract_v12_5.md", text)
    write_text(ROOT / "docs/replay/replay_contract_v12_5.md", text)
    write_text(ROOT / "releases/replay_contract_v12_5/README.md", text)

    svg = build_svg(summary)
    write_text(ROOT / "visuals/replay/v12_5_replay_contract.svg", svg)

    print(json.dumps({
        "passed": True,
        "schema": package["schema"],
        "summary": summary,
        "outputs": [
            "reports/replay/replay_contract_v12_5.json",
            "reports/replay/replay_contract_v12_5.md",
            "docs/replay/replay_contract_v12_5.md",
            "docs/context/replay_contract_index_v12_5.json",
            "visuals/replay/v12_5_replay_contract.svg",
            "releases/replay_contract_v12_5/README.md"
        ],
        "claim_boundary": "Replay contracts classify reproducibility readiness only."
    }, indent=2))

    return 0

if __name__ == "__main__":
    raise SystemExit(main())