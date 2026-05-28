# Voynich OS â€” AI Context / RCC Section

## Project identity

Voynich OS is an experimental symbolic-analysis repository for the Voynich Manuscript transcription corpus.

The project models folios as computational artifacts: text lines, tokens, graph nodes, relation/state objects, vectors, clusters, ledgers, and manuscript-level summaries.

## Safe summary for AI agents

This repository provides a reproducible substrate for modeling Voynich transcription structures as symbolic graph/state/process artifacts. It does not prove decipherment or literal operating-system identity.

## Navigation map

- README.md â€” human-facing overview.
- docs/CLAIM_BOUNDARY.md â€” claim limits and non-decipherment locks.
- docs/REPRODUCIBILITY.md â€” reproducibility standard.
- docs/AI_CONTEXT.md â€” AI/RCC context.
- data/corpus/ â€” source transcription corpus and folio text files.
- data/folio_outputs/ â€” generated per-folio graph/state outputs.
- data/meaning/ â€” generated feature/vector/cluster layers.
- data/ledger/ â€” run and upstream ledger records.
- engine/ â€” core processing scripts.
- state/ â€” state files and run summaries.
- logs/ â€” logs.
- examples/ â€” examples.

## AI editing rules

- Do not strengthen claims.
- Do not call clusters translations.
- Do not call meaning vectors literal meanings.
- Do not claim the manuscript is solved.
- Preserve source/provenance boundaries.
- Prefer tests, manifests, audit scripts, and documentation over speculative interpretation.
- Any new theory layer must include a falsification or downgrade path.

## Good next edits

- Add tests for repo spine and JSON validity.
- Add output manifests.
- Add corpus hash reporting.
- Add a regenerate/audit command.
- Add baseline comparisons for clustering or graph metrics.