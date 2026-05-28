from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

MANIFEST_PATH = ROOT / "state/manifests/voynich_output_manifest_v12_3.json"

CLAIM_LOCKS = [
    "Modeling is not decipherment.",
    "Structure is not translation.",
    "Clusters are not meaning.",
    "Generated outputs are task-bounded artifacts, not universal proof.",
    "Output manifests prove artifact observability, not decipherment or translation.",
    "Validation remains required."
]

SHOWCASE_DOES_NOT_PROVE = [
    "decipherment",
    "translation",
    "literal_operating_system_identity",
    "authorial_intent",
    "validated_semantic_meaning",
    "historical_truth",
    "production_readiness"
]

def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def safe_pct(part: int, whole: int) -> float:
    if whole <= 0:
        return 0.0
    return round((part / whole) * 100.0, 3)

def family_table(families: list[dict[str, Any]]) -> str:
    rows = []
    rows.append("| Family | Files | Bytes | Current path | Alias | Claim boundary |")
    rows.append("|---|---:|---:|---|---|---|")
    for f in families:
        rows.append(
            f"| {f['title']} | {f['file_count']} | {f['total_bytes']} | "
            f"`{f['current_path']}` | `{f['professional_alias']}` | {f['claim_boundary']} |"
        )
    return "\n".join(rows)

def top_family_table(families: list[dict[str, Any]]) -> str:
    ranked = sorted(families, key=lambda f: (f.get("file_count", 0), f.get("total_bytes", 0)), reverse=True)
    rows = []
    rows.append("| Rank | Family | Files | Share of files | Bytes |")
    rows.append("|---:|---|---:|---:|---:|")
    total_files = sum(f.get("file_count", 0) for f in families)
    for i, f in enumerate(ranked, start=1):
        rows.append(
            f"| {i} | {f['title']} | {f['file_count']} | {safe_pct(f['file_count'], total_files)}% | {f['total_bytes']} |"
        )
    return "\n".join(rows)

def alias_table(aliases: list[dict[str, Any]]) -> str:
    rows = []
    rows.append("| Current path | Professional alias | Status | Rule |")
    rows.append("|---|---|---|---|")
    for a in aliases:
        rows.append(
            f"| `{a['current_path']}` | `{a['professional_alias']}` | {a['status']} | {a['claim_boundary']} |"
        )
    return "\n".join(rows)

def build_svg(families: list[dict[str, Any]], totals: dict[str, Any]) -> str:
    ranked = sorted(families, key=lambda f: f.get("file_count", 0), reverse=True)[:8]
    max_files = max([f.get("file_count", 0) for f in ranked] + [1])

    bars = []
    y = 150
    for f in ranked:
        width = int(500 * (f.get("file_count", 0) / max_files))
        label = f["family_id"].replace("_", " ")
        bars.append(f'<text x="80" y="{y + 18}" font-family="Arial" font-size="14">{label}</text>')
        bars.append(f'<rect x="330" y="{y}" width="{width}" height="24" fill="#d9d9d9" stroke="#222"/>')
        bars.append(f'<text x="{340 + width}" y="{y + 18}" font-family="Arial" font-size="13">{f.get("file_count", 0)} files</text>')
        y += 42

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="680" viewBox="0 0 1200 680">
  <rect width="1200" height="680" fill="#ffffff"/>
  <text x="60" y="60" font-family="Arial" font-size="30" font-weight="bold">Voynich OS v12.4 Showcase Evidence Atlas</text>
  <text x="60" y="98" font-family="Arial" font-size="17">Artifact observability package built from the v12.3 output manifest.</text>

  <rect x="60" y="120" width="1080" height="430" rx="18" fill="#f7f7f7" stroke="#222"/>
  <text x="80" y="145" font-family="Arial" font-size="18" font-weight="bold">Top manifested artifact families by file count</text>
  {''.join(bars)}

  <rect x="60" y="585" width="330" height="55" rx="12" fill="#f2f2f2" stroke="#222"/>
  <text x="80" y="617" font-family="Arial" font-size="18">Families: {totals.get("families", 0)}</text>

  <rect x="430" y="585" width="330" height="55" rx="12" fill="#f2f2f2" stroke="#222"/>
  <text x="450" y="617" font-family="Arial" font-size="18">Files: {totals.get("files", 0)}</text>

  <rect x="800" y="585" width="340" height="55" rx="12" fill="#f2f2f2" stroke="#222"/>
  <text x="820" y="617" font-family="Arial" font-size="18">Bytes: {totals.get("bytes", 0)}</text>

  <text x="60" y="665" font-family="Arial" font-size="14">Non-claim lock: artifact observability is not decipherment, translation, semantic proof, or literal OS proof.</text>
</svg>
'''

def main() -> int:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"Missing v12.3 manifest: {MANIFEST_PATH}")

    manifest = read_json(MANIFEST_PATH)
    families = manifest.get("families", [])
    aliases = manifest.get("aliases", [])
    totals = manifest.get("totals", {})

    if manifest.get("schema") != "voynich-os-output-manifest-v12.3":
        raise SystemExit("v12.3 manifest schema mismatch")

    if not families:
        raise SystemExit("v12.3 manifest contains no families")

    timestamp = datetime.now(timezone.utc).isoformat()
    package = {
        "schema": "voynich-os-showcase-evidence-package-v12.4",
        "timestamp_utc": timestamp,
        "checkpoint": "Voynich OS v12.4 - Showcase Evidence Package and Visual Atlas",
        "source_manifest": "state/manifests/voynich_output_manifest_v12_3.json",
        "source_manifest_schema": manifest.get("schema"),
        "purpose": "Package selected manifest evidence, visual atlas, route aliases, and claim boundaries into a public showcase layer.",
        "public_demonstration_claim": "Voynich OS can demonstrate a governed artifact chain: corpus, generated outputs, diagnostic vectors, manuscript state, ledgers, audits, RCC route maps, output manifests, aliases, and showcase surfaces.",
        "totals": totals,
        "top_families_by_file_count": sorted(
            [
                {
                    "family_id": f["family_id"],
                    "title": f["title"],
                    "file_count": f["file_count"],
                    "total_bytes": f["total_bytes"],
                    "current_path": f["current_path"],
                    "professional_alias": f["professional_alias"],
                    "claim_boundary": f["claim_boundary"]
                }
                for f in families
            ],
            key=lambda x: (x["file_count"], x["total_bytes"]),
            reverse=True
        ),
        "aliases": aliases,
        "claim_locks": CLAIM_LOCKS,
        "does_not_prove": SHOWCASE_DOES_NOT_PROVE,
        "showcase_chain": [
            "corpus",
            "folio_outputs",
            "meaning_vector_diagnostics",
            "manuscript_state",
            "ledgers",
            "repo_audits",
            "rcc_nexus",
            "output_manifest",
            "path_aliases",
            "showcase_package",
            "visual_atlas"
        ],
        "next_layer": {
            "recommended": "Voynich OS v12.5 - Reproducibility Replay Contract",
            "reason": "After outputs are showcased, the next proof layer should define which artifacts can be regenerated, by which command, from which inputs, with which expected hashes or tolerances."
        }
    }

    write_json(ROOT / "releases/showcase_v12_4/showcase_evidence_package_v12_4.json", package)
    write_json(ROOT / "reports/showcase/v12_4/latest_showcase_evidence_package_v12_4.json", package)

    readme = []
    readme.append("# Voynich OS v12.4 - Showcase Evidence Package")
    readme.append("")
    readme.append("## Purpose")
    readme.append("")
    readme.append("This release packages the v12.3 output manifest into a public evidence showcase.")
    readme.append("")
    readme.append("It demonstrates repository observability: artifact families, counts, hashes, aliases, route surfaces, and claim boundaries.")
    readme.append("")
    readme.append("## Public demonstration claim")
    readme.append("")
    readme.append(package["public_demonstration_claim"])
    readme.append("")
    readme.append("## What this proves")
    readme.append("")
    readme.append("- The repository can inventory and route its generated artifact field.")
    readme.append("- The repository can expose artifact-family counts and hashes.")
    readme.append("- The repository can separate current paths from professional aliases.")
    readme.append("- The repository can publish a visual evidence atlas without strengthening manuscript claims.")
    readme.append("- The repository can preserve non-claim locks while becoming more demonstrable.")
    readme.append("")
    readme.append("## What this does not prove")
    readme.append("")
    for item in SHOWCASE_DOES_NOT_PROVE:
        readme.append(f"- {item}")
    readme.append("")
    readme.append("## Totals")
    readme.append("")
    readme.append("| Metric | Value |")
    readme.append("|---|---:|")
    readme.append(f"| Families | {totals.get('families', 0)} |")
    readme.append(f"| Files | {totals.get('files', 0)} |")
    readme.append(f"| Bytes | {totals.get('bytes', 0)} |")
    readme.append("")
    readme.append("## Top artifact families")
    readme.append("")
    readme.append(top_family_table(families))
    readme.append("")
    readme.append("## All artifact families")
    readme.append("")
    readme.append(family_table(families))
    readme.append("")
    readme.append("## Path aliases")
    readme.append("")
    readme.append(alias_table(aliases))
    readme.append("")
    readme.append("## Showcase chain")
    readme.append("")
    readme.append("corpus -> folio outputs -> meaning/vector diagnostics -> manuscript state -> ledgers -> audits -> RCC Nexus -> output manifest -> alias plan -> showcase package -> visual atlas")
    readme.append("")
    readme.append("## Primary files")
    readme.append("")
    readme.append("- `releases/showcase_v12_4/showcase_evidence_package_v12_4.json`")
    readme.append("- `releases/showcase_v12_4/README.md`")
    readme.append("- `reports/showcase/v12_4/latest_showcase_evidence_package_v12_4.json`")
    readme.append("- `reports/showcase/v12_4/latest_showcase_evidence_package_v12_4.md`")
    readme.append("- `docs/showcase/showcase_atlas_v12_4.md`")
    readme.append("- `visuals/showcase/v12_4/showcase_evidence_atlas.svg`")
    readme.append("")
    readme.append("## Non-claim lock")
    readme.append("")
    for lock in CLAIM_LOCKS:
        readme.append(f"- {lock}")
    readme.append("")
    readme.append("## Next layer")
    readme.append("")
    readme.append("Voynich OS v12.5 - Reproducibility Replay Contract")
    readme.append("")
    readme.append("Recommended purpose: define which artifacts can be regenerated, by which command, from which inputs, with which expected hashes or tolerated drift.")
    readme.append("")

    release_readme = "\n".join(readme)
    write_text(ROOT / "releases/showcase_v12_4/README.md", release_readme)
    write_text(ROOT / "reports/showcase/v12_4/latest_showcase_evidence_package_v12_4.md", release_readme)

    atlas = []
    atlas.append("# Voynich OS v12.4 - Visual Showcase Atlas")
    atlas.append("")
    atlas.append("![Voynich OS v12.4 Showcase Evidence Atlas](../../visuals/showcase/v12_4/showcase_evidence_atlas.svg)")
    atlas.append("")
    atlas.append("## Atlas purpose")
    atlas.append("")
    atlas.append("The atlas compresses the v12.3 output manifest into a human-readable demonstration surface.")
    atlas.append("")
    atlas.append("## Atlas interpretation")
    atlas.append("")
    atlas.append("The chart shows manifested artifact-family scale. It is a repository-observability chart, not a decipherment chart.")
    atlas.append("")
    atlas.append("## Reading rule")
    atlas.append("")
    atlas.append("A taller artifact family means more generated/recorded files in that family. It does not mean higher truth, higher semantic validity, or stronger manuscript interpretation.")
    atlas.append("")
    atlas.append("## Non-claim lock")
    atlas.append("")
    atlas.append("Visual evidence is not semantic proof. Charts improve observability, not decipherment.")
    atlas.append("")

    write_text(ROOT / "docs/showcase/showcase_atlas_v12_4.md", "\n".join(atlas))

    svg = build_svg(families, totals)
    write_text(ROOT / "visuals/showcase/v12_4/showcase_evidence_atlas.svg", svg)

    index = {
        "schema": "voynich-os-showcase-index-v12.4",
        "timestamp_utc": timestamp,
        "checkpoint": "Voynich OS v12.4 - Showcase Evidence Package and Visual Atlas",
        "showcase_files": [
            "releases/showcase_v12_4/README.md",
            "releases/showcase_v12_4/showcase_evidence_package_v12_4.json",
            "reports/showcase/v12_4/latest_showcase_evidence_package_v12_4.md",
            "reports/showcase/v12_4/latest_showcase_evidence_package_v12_4.json",
            "docs/showcase/showcase_atlas_v12_4.md",
            "visuals/showcase/v12_4/showcase_evidence_atlas.svg"
        ],
        "source_files": [
            "state/manifests/voynich_output_manifest_v12_3.json",
            "reports/output_manifest/latest_output_manifest_v12_3.md",
            "docs/context/path_aliases_v12_3.json"
        ],
        "claim_boundary": "Showcase evidence packages prove artifact observability and public communication readiness only. They do not prove decipherment or translation."
    }

    write_json(ROOT / "docs/context/showcase_index_v12_4.json", index)

    print(json.dumps({
        "passed": True,
        "schema": package["schema"],
        "totals": totals,
        "outputs": index["showcase_files"],
        "claim_boundary": index["claim_boundary"]
    }, indent=2))

    return 0

if __name__ == "__main__":
    raise SystemExit(main())