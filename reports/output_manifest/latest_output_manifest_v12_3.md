# Voynich OS v12.3 - Output Manifest and Alias Layer

## Purpose

v12.3 makes the generated artifact surface inspectable before any folder migration.

The rule is simple: do not move evidence before naming it, hashing it, counting it, and assigning its claim boundary.

## What this proves

- The repo can inventory its major output families.
- The repo can hash representative and full family files.
- The repo can expose current paths and professional aliases.
- The repo can preserve claim boundaries per artifact family.

## What this does not prove

- decipherment
- translation
- authorial_intent
- literal_operating_system_identity
- validated_semantic_meaning
- historical_truth

## Manifest totals

| Metric | Value |
|---|---:|
| Families | 10 |
| Files | 1019 |
| Bytes | 38670707 |

## Artifact families

| Family | Current path | Alias | Files | Boundary |
|---|---|---|---:|---|
| Corpus text files | `data/corpus` | `datasets/corpus/` | 229 | Corpus files are source material for modeling; they are not decipherment. |
| Corpus JSON files | `data/corpus` | `datasets/corpus/` | 1 | Corpus JSON is source/metadata structure, not semantic proof. |
| Folio output JSON files | `data/folio_outputs` | `outputs/folio_graphs/` | 226 | Folio outputs are symbolic diagnostics, not translation. |
| Meaning/vector JSON files | `data/meaning` | `outputs/semantic_diagnostics/` | 546 | Meaning vectors and clusters are diagnostics, not literal meanings. |
| Manuscript-level state JSON files | `data/manuscript_v12_0` | `outputs/manuscript_state/` | 2 | Manuscript-level state is synthesis output, not proof of authorial intent. |
| Ledger JSONL files | `data/ledger` | `ledgers/` | 2 | Ledgers record process history, not correctness proof. |
| State audit JSON files | `state/audits` | `state/audits/` | 2 | Audit state records observed repo properties, not manuscript interpretation. |
| RCC Nexus reports | `reports/rcc_nexus` | `reports/rcc_nexus/` | 2 | RCC-N validates navigation, not code correctness or decipherment. |
| README audit reports | `reports/readme` | `reports/readme/` | 2 | README audits validate public framing, not manuscript meaning. |
| Documentation Markdown files | `docs` | `docs/` | 7 | Documentation guides interpretation; it is not evidence by itself. |

## Primary outputs

- `state/manifests/voynich_output_manifest_v12_3.json`
- `state/manifests/families/`
- `reports/output_manifest/latest_output_manifest_v12_3.json`
- `reports/output_manifest/latest_output_manifest_v12_3.md`
- `docs/context/path_aliases_v12_3.json`
- `reports/reorg/path_alias_plan_v12_3.md`
- `reports/showcase/voynich_os_showcase_v12_3.md`

## Next layer

Voynich OS v12.4 - Showcase Evidence Package and Visual Atlas

Recommended purpose: package the strongest visible evidence surfaces into a public demonstration bundle without strengthening the manuscript claim.
