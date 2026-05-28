# tests

## Folder Purpose

Executable validation tests.

## RCC Nexus Echo Location

| Field | Value |
|---|---|
| Shell | middle |
| Meridian(s) | validation, runtime |
| Sector | tests |
| Version / TTL | RCC-N-v1.7 / 180 days |
| Last verified | 2026-05-28 |
| Local role | Executable validation tests. |

## Evidence Surface

tests/test_repo_spine.py

## Validation Surface

    python -m pytest -q

## Claim Boundary

This mini README improves local navigation and agent orientation. It does not prove code correctness, patch safety, empirical validation, decipherment, translation, literal meaning, AI understanding, or production readiness.

## Non-Claim Locks

- navigation_is_not_validation
- documentation_is_not_correctness
- modeling_is_not_decipherment
- structure_is_not_translation
- clusters_are_not_meaning
- validation_remains_required

## Agent Route

Read root README, README_90_SECONDS.md, AGENTS.md, docs/context indexes, route map, then this README before editing.

## Update Obligation

Update this README and RCC/Nexus records if folder purpose, hooks, evidence surfaces, validation commands, or claim boundaries change.

<!-- MINI_README_UPDATE_RULE_START -->
## AI Update Rule - Mini README and Directory Box Synchronization

This folder is part of the RCC-N navigable repository surface.

When this folder's purpose, files, routes, evidence surfaces, validation commands, or claim boundaries change, update this mini README in the same commit. Also update the root README directory spine if any folder is added, removed, renamed, or repurposed.

Required after relevant changes:

    python scripts/rcc/check_rcc_nexus.py
    python scripts/rcc/audit_readme_surface.py
    python -m pytest -q

Non-claim lock: navigation is not validation, but stale navigation is repository drift.
<!-- MINI_README_UPDATE_RULE_END -->