# Voynich OS - Agent Operating Contract

## Project identity

Voynich OS is an experimental symbolic-analysis repository for the Voynich Manuscript transcription corpus.

It models transcription structures as computational artifacts: folio text, tokens, graph/state objects, feature vectors, clusters, ledgers, audit outputs, and manuscript-level summaries.

## Non-claim boundary

Voynich OS does not prove decipherment.

Voynich OS does not prove translation.

Voynich OS does not prove that the Voynich Manuscript is literally an operating system.

Voynich OS tests whether Voynich transcription structures can be modeled as symbolic graph/state/process systems and whether those models emit stable, inspectable, reproducible diagnostic artifacts.

## Required read order before editing

1. README.md
2. README_90_SECONDS.md
3. AGENTS.md
4. docs/context/repository_context_index.json
5. docs/context/rcc_nexus_index.json
6. rcc/nexus/route_map.json
7. rcc/nexus/task_routing_matrix.md
8. Target folder README.md
9. Relevant source, tests, state, and reports

## Patch discipline

Every patch must identify:

- affected folder;
- affected route;
- validation command;
- claim boundary;
- generated artifacts;
- whether tests were run.

## Required validation after RCC or documentation changes

    python scripts/rcc/check_rcc_nexus.py
    python scripts/rcc/audit_readme_surface.py
    python -m pytest -q

## Required validation after JSON, state, or output changes

    python scripts/normalize_json_utf8.py
    python scripts/voynich_repo_audit.py
    python -m pytest -q

## Failure learning rule

If an AI or human patch causes a failure, add the lesson to the relevant README, report, or docs surface before promotion.

Failure logs are repository memory, not blame records.

## Claim lock

Navigation is not validation.

Documentation is not correctness.

Modeling is not decipherment.

Clusters are not translation.

Validation remains required.