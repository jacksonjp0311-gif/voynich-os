from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

RUN_ID = datetime.now(timezone.utc).strftime("v12_3_%Y%m%d_%H%M%S_utc")

CLAIM_BOUNDARY = {
    "safe_claim": "Voynich OS can inventory, hash, route, and audit generated symbolic-analysis artifacts from the Voynich transcription corpus.",
    "does_not_prove": [
        "decipherment",
        "translation",
        "authorial_intent",
        "literal_operating_system_identity",
        "validated_semantic_meaning",
        "historical_truth"
    ],
    "locks": [
        "Modeling is not decipherment.",
        "Structure is not translation.",
        "Clusters are not meaning.",
        "Generated outputs are task-bounded artifacts, not universal proof.",
        "Validation remains required."
    ]
}

ALIASES = [
    {
        "current_path": "data/corpus/",
        "professional_alias": "datasets/corpus/",
        "status": "preserve_current_path",
        "reason": "Source corpus path is active and should remain stable until package-level migration is planned.",
        "claim_boundary": "Corpus presence is not translation or decipherment."
    },
    {
        "current_path": "data/folio_outputs/",
        "professional_alias": "outputs/folio_graphs/",
        "status": "alias_only_no_move",
        "reason": "Generated folio JSON artifacts must be manifested before any folder migration.",
        "claim_boundary": "Folio graph outputs are diagnostics, not proof of manuscript meaning."
    },
    {
        "current_path": "data/meaning/",
        "professional_alias": "outputs/semantic_diagnostics/",
        "status": "alias_only_no_move",
        "reason": "Meaning/vector outputs are structurally important but semantically bounded.",
        "claim_boundary": "Meaning vectors are diagnostics, not validated semantic readings."
    },
    {
        "current_path": "data/manuscript_v12_0/",
        "professional_alias": "outputs/manuscript_state/",
        "status": "alias_only_no_move",
        "reason": "Manuscript-level synthesis state requires stable provenance.",
        "claim_boundary": "Manuscript state is synthesis output, not proof of decipherment."
    },
    {
        "current_path": "data/ledger/",
        "professional_alias": "ledgers/",
        "status": "alias_only_no_move",
        "reason": "Ledger path is active; future move requires backward-compatible route update.",
        "claim_boundary": "Ledger continuity records process history, not correctness proof."
    },
    {
        "current_path": "export_v4_5/",
        "professional_alias": "legacy/export_v4_5/",
        "status": "preserve_until_legacy_migration",
        "reason": "Legacy export surface should not be moved until route aliases and references are audited.",
        "claim_boundary": "Legacy output preservation is reproducibility support, not validation."
    },
    {
        "current_path": "import_v4_5/",
        "professional_alias": "legacy/import_v4_5/",
        "status": "preserve_until_legacy_migration",
        "reason": "Legacy import surface should not be moved until route aliases and references are audited.",
        "claim_boundary": "Legacy input preservation is reproducibility support, not validation."
    }
]

FAMILIES = [
    {
        "family_id": "corpus_txt",
        "title": "Corpus text files",
        "path": "data/corpus",
        "patterns": ["**/*.txt"],
        "role": "Source transcription text surface.",
        "professional_alias": "datasets/corpus/",
        "claim_boundary": "Corpus files are source material for modeling; they are not decipherment."
    },
    {
        "family_id": "corpus_json",
        "title": "Corpus JSON files",
        "path": "data/corpus",
        "patterns": ["**/*.json"],
        "role": "Structured corpus-side source or metadata surface.",
        "professional_alias": "datasets/corpus/",
        "claim_boundary": "Corpus JSON is source/metadata structure, not semantic proof."
    },
    {
        "family_id": "folio_outputs_json",
        "title": "Folio output JSON files",
        "path": "data/folio_outputs",
        "patterns": ["**/*.json"],
        "role": "Generated folio graph/state artifacts.",
        "professional_alias": "outputs/folio_graphs/",
        "claim_boundary": "Folio outputs are symbolic diagnostics, not translation."
    },
    {
        "family_id": "meaning_json",
        "title": "Meaning/vector JSON files",
        "path": "data/meaning",
        "patterns": ["**/*.json"],
        "role": "Generated meaning/vector/cluster diagnostic artifacts.",
        "professional_alias": "outputs/semantic_diagnostics/",
        "claim_boundary": "Meaning vectors and clusters are diagnostics, not literal meanings."
    },
    {
        "family_id": "manuscript_state_json",
        "title": "Manuscript-level state JSON files",
        "path": "data/manuscript_v12_0",
        "patterns": ["**/*.json"],
        "role": "Manuscript-level synthesis and state artifacts.",
        "professional_alias": "outputs/manuscript_state/",
        "claim_boundary": "Manuscript-level state is synthesis output, not proof of authorial intent."
    },
    {
        "family_id": "ledger_jsonl",
        "title": "Ledger JSONL files",
        "path": "data/ledger",
        "patterns": ["**/*.jsonl"],
        "role": "Append-style ledger and run-history surfaces.",
        "professional_alias": "ledgers/",
        "claim_boundary": "Ledgers record process history, not correctness proof."
    },
    {
        "family_id": "state_audits",
        "title": "State audit JSON files",
        "path": "state/audits",
        "patterns": ["**/*.json"],
        "role": "Repository audit and validation state.",
        "professional_alias": "state/audits/",
        "claim_boundary": "Audit state records observed repo properties, not manuscript interpretation."
    },
    {
        "family_id": "rcc_reports",
        "title": "RCC Nexus reports",
        "path": "reports/rcc_nexus",
        "patterns": ["**/*.json", "**/*.md"],
        "role": "RCC-N route and mini README validation reports.",
        "professional_alias": "reports/rcc_nexus/",
        "claim_boundary": "RCC-N validates navigation, not code correctness or decipherment."
    },
    {
        "family_id": "readme_reports",
        "title": "README audit reports",
        "path": "reports/readme",
        "patterns": ["**/*.json", "**/*.md"],
        "role": "README and mini repo discipline reports.",
        "professional_alias": "reports/readme/",
        "claim_boundary": "README audits validate public framing, not manuscript meaning."
    },
    {
        "family_id": "docs_md",
        "title": "Documentation Markdown files",
        "path": "docs",
        "patterns": ["**/*.md"],
        "role": "Claim boundary, reproducibility, AI context, archive, and documentation surfaces.",
        "professional_alias": "docs/",
        "claim_boundary": "Documentation guides interpretation; it is not evidence by itself."
    }
]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def collect_family(family: dict[str, Any]) -> dict[str, Any]:
    base = ROOT / family["path"]
    files: list[Path] = []

    if base.exists():
        for pattern in family["patterns"]:
            files.extend(base.glob(pattern))

    files = sorted(set(p for p in files if p.is_file()), key=lambda p: p.as_posix())

    entries = []
    total_bytes = 0

    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        size = p.stat().st_size
        total_bytes += size
        entries.append({
            "path": rel,
            "bytes": size,
            "sha256": sha256_file(p)
        })

    family_manifest = {
        "family_id": family["family_id"],
        "title": family["title"],
        "current_path": family["path"],
        "professional_alias": family["professional_alias"],
        "role": family["role"],
        "claim_boundary": family["claim_boundary"],
        "file_count": len(entries),
        "total_bytes": total_bytes,
        "sample_hashes": entries[:10],
        "all_files": entries
    }

    return family_manifest

def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def main() -> int:
    families = [collect_family(f) for f in FAMILIES]

    totals = {
        "families": len(families),
        "files": sum(f["file_count"] for f in families),
        "bytes": sum(f["total_bytes"] for f in families)
    }

    manifest = {
        "schema": "voynich-os-output-manifest-v12.3",
        "run_id": RUN_ID,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(ROOT),
        "checkpoint": "Voynich OS v12.3 - Output Manifest and Alias Layer",
        "purpose": "Inventory, hash, classify, and route generated artifact families before any professional folder migration.",
        "claim_boundary": CLAIM_BOUNDARY,
        "totals": totals,
        "aliases": ALIASES,
        "families": families,
        "next_layer": {
            "recommended": "Voynich OS v12.4 - Showcase Evidence Package and Visual Atlas",
            "reason": "After outputs are manifested, the repo can package selected evidence surfaces for public demonstration without changing claim strength."
        }
    }

    for family in families:
        family_path = ROOT / "state/manifests/families" / f"{family['family_id']}_manifest_v12_3.json"
        write_json(family_path, family)

    write_json(ROOT / "state/manifests/voynich_output_manifest_v12_3.json", manifest)
    write_json(ROOT / "reports/output_manifest/latest_output_manifest_v12_3.json", manifest)
    write_json(ROOT / "docs/context/path_aliases_v12_3.json", {
        "schema": "voynich-os-path-aliases-v12.3",
        "timestamp_utc": manifest["timestamp_utc"],
        "purpose": "Define professional route aliases before moving any active generated output directories.",
        "aliases": ALIASES,
        "migration_allowed": False,
        "migration_rule": "No active generated folder may be moved until manifests, aliases, README surfaces, and tests all pass.",
        "claim_boundary": "Path aliases improve navigation and migration planning; they do not validate outputs or decipher the manuscript."
    })

    md = []
    md.append("# Voynich OS v12.3 - Output Manifest and Alias Layer")
    md.append("")
    md.append("## Purpose")
    md.append("")
    md.append("v12.3 makes the generated artifact surface inspectable before any folder migration.")
    md.append("")
    md.append("The rule is simple: do not move evidence before naming it, hashing it, counting it, and assigning its claim boundary.")
    md.append("")
    md.append("## What this proves")
    md.append("")
    md.append("- The repo can inventory its major output families.")
    md.append("- The repo can hash representative and full family files.")
    md.append("- The repo can expose current paths and professional aliases.")
    md.append("- The repo can preserve claim boundaries per artifact family.")
    md.append("")
    md.append("## What this does not prove")
    md.append("")
    for item in CLAIM_BOUNDARY["does_not_prove"]:
        md.append(f"- {item}")
    md.append("")
    md.append("## Manifest totals")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|---|---:|")
    md.append(f"| Families | {totals['families']} |")
    md.append(f"| Files | {totals['files']} |")
    md.append(f"| Bytes | {totals['bytes']} |")
    md.append("")
    md.append("## Artifact families")
    md.append("")
    md.append("| Family | Current path | Alias | Files | Boundary |")
    md.append("|---|---|---|---:|---|")
    for f in families:
        md.append(f"| {f['title']} | `{f['current_path']}` | `{f['professional_alias']}` | {f['file_count']} | {f['claim_boundary']} |")
    md.append("")
    md.append("## Primary outputs")
    md.append("")
    md.append("- `state/manifests/voynich_output_manifest_v12_3.json`")
    md.append("- `state/manifests/families/`")
    md.append("- `reports/output_manifest/latest_output_manifest_v12_3.json`")
    md.append("- `reports/output_manifest/latest_output_manifest_v12_3.md`")
    md.append("- `docs/context/path_aliases_v12_3.json`")
    md.append("- `reports/reorg/path_alias_plan_v12_3.md`")
    md.append("- `reports/showcase/voynich_os_showcase_v12_3.md`")
    md.append("")
    md.append("## Next layer")
    md.append("")
    md.append("Voynich OS v12.4 - Showcase Evidence Package and Visual Atlas")
    md.append("")
    md.append("Recommended purpose: package the strongest visible evidence surfaces into a public demonstration bundle without strengthening the manuscript claim.")
    md.append("")

    write_text(ROOT / "reports/output_manifest/latest_output_manifest_v12_3.md", "\n".join(md))

    alias_md = []
    alias_md.append("# Voynich OS v12.3 - Path Alias Plan")
    alias_md.append("")
    alias_md.append("## Rule")
    alias_md.append("")
    alias_md.append("No active generated folder is moved in v12.3. This layer creates professional aliases only.")
    alias_md.append("")
    alias_md.append("| Current path | Professional alias | Status | Reason |")
    alias_md.append("|---|---|---|---|")
    for a in ALIASES:
        alias_md.append(f"| `{a['current_path']}` | `{a['professional_alias']}` | {a['status']} | {a['reason']} |")
    alias_md.append("")
    alias_md.append("## Claim boundary")
    alias_md.append("")
    alias_md.append("Aliases improve navigation and future migration safety. They do not validate outputs, prove decipherment, or prove translation.")
    alias_md.append("")

    write_text(ROOT / "reports/reorg/path_alias_plan_v12_3.md", "\n".join(alias_md))

    showcase = []
    showcase.append("# Voynich OS v12.3 - Showcase Brief")
    showcase.append("")
    showcase.append("## Public demonstration claim")
    showcase.append("")
    showcase.append("Voynich OS can now showcase a governed artifact chain: corpus, generated outputs, diagnostic vectors, manuscript state, audits, RCC route maps, and output manifests.")
    showcase.append("")
    showcase.append("## Showcase chain")
    showcase.append("")
    showcase.append("corpus -> folio outputs -> meaning/vector diagnostics -> manuscript state -> ledgers -> audits -> RCC Nexus -> output manifest -> alias plan")
    showcase.append("")
    showcase.append("## What we learned")
    showcase.append("")
    showcase.append("The repo became clearer after the public README was converted from discovery narrative to evidence-bounded runtime framing. v12.3 extends that clarity from the README into the artifact surface.")
    showcase.append("")
    showcase.append("## What can be shown")
    showcase.append("")
    showcase.append("| Evidence surface | What it demonstrates |")
    showcase.append("|---|---|")
    showcase.append("| `state/manifests/voynich_output_manifest_v12_3.json` | Full artifact-family manifest. |")
    showcase.append("| `state/manifests/families/` | Per-family file inventories and hashes. |")
    showcase.append("| `reports/output_manifest/latest_output_manifest_v12_3.md` | Human-readable evidence overview. |")
    showcase.append("| `docs/context/path_aliases_v12_3.json` | Professional path aliases without destructive migration. |")
    showcase.append("| `reports/reorg/path_alias_plan_v12_3.md` | Migration discipline and path boundary. |")
    showcase.append("")
    showcase.append("## Non-claim lock")
    showcase.append("")
    showcase.append("This showcase proves repository discipline and artifact observability. It does not prove decipherment, translation, or literal operating-system identity.")
    showcase.append("")

    write_text(ROOT / "reports/showcase/voynich_os_showcase_v12_3.md", "\n".join(showcase))

    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="520" viewBox="0 0 1200 520">
  <rect width="1200" height="520" fill="#ffffff"/>
  <text x="60" y="60" font-family="Arial" font-size="30" font-weight="bold">Voynich OS v12.3 Output Manifest Layer</text>
  <text x="60" y="100" font-family="Arial" font-size="18">corpus -> outputs -> diagnostics -> state -> ledgers -> audits -> RCC -> manifest -> alias plan</text>
  <g font-family="Arial" font-size="16">
    <rect x="60" y="150" width="120" height="70" rx="12" fill="#f2f2f2" stroke="#222"/>
    <text x="90" y="192">Corpus</text>
    <rect x="200" y="150" width="120" height="70" rx="12" fill="#f2f2f2" stroke="#222"/>
    <text x="230" y="192">Folios</text>
    <rect x="340" y="150" width="140" height="70" rx="12" fill="#f2f2f2" stroke="#222"/>
    <text x="365" y="192">Diagnostics</text>
    <rect x="500" y="150" width="120" height="70" rx="12" fill="#f2f2f2" stroke="#222"/>
    <text x="535" y="192">State</text>
    <rect x="640" y="150" width="120" height="70" rx="12" fill="#f2f2f2" stroke="#222"/>
    <text x="675" y="192">Ledger</text>
    <rect x="780" y="150" width="120" height="70" rx="12" fill="#f2f2f2" stroke="#222"/>
    <text x="815" y="192">Audit</text>
    <rect x="920" y="150" width="120" height="70" rx="12" fill="#f2f2f2" stroke="#222"/>
    <text x="955" y="192">RCC</text>
    <rect x="500" y="300" width="200" height="80" rx="14" fill="#e8e8e8" stroke="#222"/>
    <text x="535" y="345">Output Manifest</text>
    <text x="545" y="368">counts + hashes</text>
    <rect x="740" y="300" width="180" height="80" rx="14" fill="#e8e8e8" stroke="#222"/>
    <text x="775" y="345">Alias Plan</text>
    <text x="760" y="368">no move before manifest</text>
  </g>
  <g stroke="#222" stroke-width="2">
    <line x1="180" y1="185" x2="200" y2="185"/>
    <line x1="320" y1="185" x2="340" y2="185"/>
    <line x1="480" y1="185" x2="500" y2="185"/>
    <line x1="620" y1="185" x2="640" y2="185"/>
    <line x1="760" y1="185" x2="780" y2="185"/>
    <line x1="900" y1="185" x2="920" y2="185"/>
    <line x1="980" y1="220" x2="620" y2="300"/>
    <line x1="700" y1="340" x2="740" y2="340"/>
  </g>
  <text x="60" y="455" font-family="Arial" font-size="16">Non-claim lock: artifact observability is not decipherment, translation, or semantic proof.</text>
</svg>
"""
    write_text(ROOT / "visuals/output_manifest/v12_3_output_manifest_layer.svg", svg)

    print(json.dumps({
        "passed": True,
        "schema": manifest["schema"],
        "run_id": RUN_ID,
        "totals": totals,
        "outputs": [
            "state/manifests/voynich_output_manifest_v12_3.json",
            "reports/output_manifest/latest_output_manifest_v12_3.md",
            "reports/showcase/voynich_os_showcase_v12_3.md",
            "docs/context/path_aliases_v12_3.json",
            "visuals/output_manifest/v12_3_output_manifest_layer.svg"
        ],
        "claim_boundary": "Output manifests prove artifact observability, not decipherment or translation."
    }, indent=2))

    return 0

if __name__ == "__main__":
    raise SystemExit(main())