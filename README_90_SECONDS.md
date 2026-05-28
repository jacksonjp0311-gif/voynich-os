# Voynich OS in 90 Seconds

Voynich OS is a local-first symbolic-analysis repository for the Voynich Manuscript transcription corpus.

It does not claim to solve or translate the manuscript.

It creates and audits computational artifacts from the corpus:

- corpus files;
- folio outputs;
- graph/state JSON;
- meaning/vector/cluster diagnostics;
- manuscript-level state;
- ledgers;
- audits;
- RCC Nexus navigation surfaces.

## Safe claim

Voynich OS tests whether Voynich transcription structures can be represented as symbolic graph/state/process systems and whether those representations produce stable, inspectable, reproducible diagnostics.

## Read first

1. README.md
2. AGENTS.md
3. docs/CLAIM_BOUNDARY.md
4. docs/REPRODUCIBILITY.md
5. docs/AI_CONTEXT.md
6. docs/context/repository_context_index.json
7. docs/context/rcc_nexus_index.json
8. rcc/nexus/route_map.json

## Validate

    python scripts/voynich_repo_audit.py
    python scripts/rcc/check_rcc_nexus.py
    python scripts/rcc/audit_readme_surface.py
    python -m pytest -q

## Current governance profile

RCC-N profile: Standard

Reason: The repo has a large generated artifact surface, public interpretive risk, and reproducibility requirements, but it is not yet a federated or critical runtime.

## Non-claim locks

- Modeling is not decipherment.
- Structure is not translation.
- Clusters are not meaning.
- Documentation is not correctness.
- RCC navigation is not validation.
- Validation remains required.