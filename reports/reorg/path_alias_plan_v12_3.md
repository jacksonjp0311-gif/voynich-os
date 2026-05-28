# Voynich OS v12.3 - Path Alias Plan

## Rule

No active generated folder is moved in v12.3. This layer creates professional aliases only.

| Current path | Professional alias | Status | Reason |
|---|---|---|---|
| `data/corpus/` | `datasets/corpus/` | preserve_current_path | Source corpus path is active and should remain stable until package-level migration is planned. |
| `data/folio_outputs/` | `outputs/folio_graphs/` | alias_only_no_move | Generated folio JSON artifacts must be manifested before any folder migration. |
| `data/meaning/` | `outputs/semantic_diagnostics/` | alias_only_no_move | Meaning/vector outputs are structurally important but semantically bounded. |
| `data/manuscript_v12_0/` | `outputs/manuscript_state/` | alias_only_no_move | Manuscript-level synthesis state requires stable provenance. |
| `data/ledger/` | `ledgers/` | alias_only_no_move | Ledger path is active; future move requires backward-compatible route update. |
| `export_v4_5/` | `legacy/export_v4_5/` | preserve_until_legacy_migration | Legacy export surface should not be moved until route aliases and references are audited. |
| `import_v4_5/` | `legacy/import_v4_5/` | preserve_until_legacy_migration | Legacy import surface should not be moved until route aliases and references are audited. |

## Claim boundary

Aliases improve navigation and future migration safety. They do not validate outputs, prove decipherment, or prove translation.
