# Voynich OS v12.2 - Professional Directory Plan

## Purpose

This plan professionalizes Voynich OS without breaking existing generated paths.

The current active repository contains large generated surfaces under data, state, logs, engine, export_v4_5, and import_v4_5. These paths are preserved in v12.2.

## Rule

Do not mass-rename active generated folders until a manifest layer records input hashes, output counts, generation status, and route aliases.

## Current-to-professional mapping

| Current path | Current role | Future professional path | v12.2 action |
|---|---|---|---|
| engine/ | active processing engine | src/voynich_os/ | preserve, document, migrate later |
| data/corpus/ | transcription corpus | datasets/corpus/ or data/corpus/ | preserve |
| data/folio_outputs/ | generated folio graph/state outputs | outputs/folio_graphs/ | preserve, manifest next |
| data/meaning/ | meaning/vector/cluster diagnostics | outputs/semantic_diagnostics/ | preserve, manifest next |
| data/ledger/ | ledgers | ledgers/ | preserve |
| state/ | state and audit state | state/ | preserve |
| logs/ | logs | logs/ | preserve |
| export_v4_5/ | legacy export | legacy/export_v4_5/ | preserve until route alias exists |
| import_v4_5/ | legacy import | legacy/import_v4_5/ | preserve until route alias exists |
| docs/ | documentation | docs/ | professionalized |
| rcc/ | RCC Nexus | rcc/ | created |
| scripts/ | scripts/checkers | scripts/ | professionalized |
| reports/ | reports | reports/ | created |
| artifacts/ | future run artifacts | artifacts/ | created |
| sources/ | future source provenance | sources/ | created |
| visuals/ | future visual evidence | visuals/ | created |
| tests/ | tests | tests/ | professionalized |

## v12.2 decision

v12.2 is a professional spine injection, not a destructive reorganization.

## v12.3 recommended layer

Voynich OS v12.3 - Output Manifest and Alias Layer

Goals:

- create manifests for every generated output family;
- record file counts, input hash, output hash sample, claim boundary, and reproducibility status;
- create route aliases for professional future names;
- only then consider safe folder migration.

## Non-claim boundary

Professional directory structure improves navigation. It does not prove decipherment, translation, correctness, or validation.