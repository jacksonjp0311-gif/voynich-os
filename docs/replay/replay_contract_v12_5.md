# Voynich OS v12.5 - Reproducibility Replay Contract

## Purpose

v12.5 answers the next proof question: which artifacts can be regenerated now, which are source-anchored, and which are observed but not replay-command mapped yet?

## Why this matters

v12.3 made the artifact field measurable. v12.4 made it showable. v12.5 makes it replay-classified.

## Summary

| Metric | Value |
|---|---:|
| Total replay contracts | 9 |
| Replayable now | 5 |
| Source anchored / verify hash | 1 |
| Observed but not replay mapped | 3 |

## Contracts

| Contract | Surface | Classification | Command | Boundary |
|---|---|---|---|---|
| `source_corpus_hash` | `data/corpus/voynich_corpus_ivtff.txt` | source_anchored_verify_hash | `python scripts/voynich_repo_audit.py` | Corpus hash verification proves source stability only, not decipherment. |
| `repo_audit_replay` | `state/audits/voynich_repo_audit_v12_1.json` | replayable_now | `python scripts/voynich_repo_audit.py` | Repo audit replay proves observable repo counts and required docs only. |
| `rcc_nexus_replay` | `reports/rcc_nexus/latest_rcc_nexus_check.json` | replayable_now | `python scripts/rcc/check_rcc_nexus.py` | RCC-N replay proves navigation-surface validity only. |
| `readme_audit_replay` | `reports/readme/latest_readme_mini_repo_audit.json` | replayable_now | `python scripts/rcc/audit_readme_surface.py` | README audit replay proves public framing checks only. |
| `output_manifest_replay` | `state/manifests/voynich_output_manifest_v12_3.json` | replayable_now | `python scripts/manifests/generate_output_manifest_v12_3.py` | Manifest replay proves artifact observability only. |
| `showcase_package_replay` | `releases/showcase_v12_4/showcase_evidence_package_v12_4.json` | replayable_now | `python scripts/showcase/build_showcase_package_v12_4.py` | Showcase replay proves package regeneration only. |
| `folio_outputs_family` | `data/folio_outputs/` | observed_not_yet_replay_mapped | `not yet mapped` | Observed folio outputs are manifested but not yet replay-command mapped. |
| `meaning_vectors_family` | `data/meaning/` | observed_not_yet_replay_mapped | `not yet mapped` | Observed meaning/vector diagnostics are manifested but not yet replay-command mapped. |
| `manuscript_state_family` | `data/manuscript_v12_0/` | observed_not_yet_replay_mapped | `not yet mapped` | Observed manuscript state is manifested but not yet replay-command mapped. |

## Claim locks

- Replay classification is not decipherment.
- Replay success is not translation.
- Hash stability is not semantic truth.
- Observed artifacts are not automatically reproducible artifacts.
- A missing replay command is a repair target, not a failure of the whole repository.
- Validation remains required.

## Next layer

Voynich OS v12.6 - Replay Evidence Package

Recommended purpose: execute the replayable contracts, capture pass/fail evidence, and convert unmapped generated families into replayable contracts where possible.
