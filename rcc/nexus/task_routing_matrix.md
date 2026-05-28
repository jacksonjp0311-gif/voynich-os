# Voynich OS - RCC Nexus Task Routing Matrix

| Change type | Read first | Validate |
|---|---|---|
| Claim boundary patch | docs/CLAIM_BOUNDARY.md, docs/AI_CONTEXT.md, README.md | python scripts/rcc/audit_readme_surface.py |
| RCC/Nexus patch | rcc/nexus/README.md, docs/context/rcc_nexus_index.json, route_map.json | python scripts/rcc/check_rcc_nexus.py |
| README patch | README.md, README_90_SECONDS.md, AGENTS.md | python scripts/rcc/audit_readme_surface.py |
| Data/output patch | docs/REPRODUCIBILITY.md, data/README.md | python scripts/normalize_json_utf8.py; python scripts/voynich_repo_audit.py |
| Engine patch | engine/README.md, tests/README.md | python -m pytest -q |
| State/log patch | state/README.md, logs/README.md | python scripts/voynich_repo_audit.py |
| Professional reorg patch | reports/reorg/professional_directory_plan_v12_2.md | RCC check + README audit + tests |

## Failure rule

If validation fails, stop promotion, patch the smallest failing surface, rerun validation, and log the reusable lesson.