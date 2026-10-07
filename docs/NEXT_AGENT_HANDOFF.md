# NBA_MIKE v2 — NEXT AGENT HANDOFF

## Current state
Project: `nba_mike_v2`
Environment: Windows / PowerShell / Python `.venv` / CPU-only / Git `main`

Last confirmed Git checkpoint before INFRA-01:
- `5b8a0a5 Complete P0-S3 S6 point-in-time snapshot system`

## Completed milestones
- P0-S3 S1 — Canonical Data Architecture
- P0-S3 S2 — Storage & Manifest Standard
- P0-S3 S3 — Canonical Identity System
- P0-S3 S4 — Schema Validation & Provenance Enforcement
- P0-S3 S5 — Canonical Dataset Builder
- P0-S3 S6 — Reproducible D-1 Point-in-Time Snapshot System; tests/acceptance PASS; committed as `5b8a0a5`.
- P0-S3 INFRA-01 — Project Packaging & Execution package prepared; run install/tests/acceptance and commit before calling complete.

## INFRA-01 purpose
A real src-layout execution defect was confirmed after S6:
- editable install failed because packaging metadata did not exist;
- standalone `import nba_mike` failed without manual `PYTHONPATH`;
- existing regression suite still passed 38 tests.

INFRA-01 adds minimal project packaging so the active `.venv` can use `python -m pip install -e .` and import `nba_mike` normally.

## Naming contract
- repository: `nba_mike_v2`
- distribution: `nba-mike-v2`
- import package: `nba_mike`

Do not rename `src/nba_mike` just to match the repository name.

## Next planned milestone after INFRA-01
Return to the original milestone plan:
- P0-S3 S7 — Leakage & Invariant Test Suite.

Do not repurpose S7 as packaging.

## Continuation discipline
1. Remove manual `PYTHONPATH`.
2. Install editable package with `python -m pip install -e .`.
3. Prove standalone import.
4. Run full pytest regression suite.
5. Run INFRA-01 acceptance.
6. Inspect git status and commit only after PASS.
7. Update development journal and this handoff at every material milestone.
8. Do not weaken gates to force PASS.
9. Do not train predictive models until the governance plan explicitly opens that gate.

## Unresolved research constraints
- Exact intraday historical truth for injuries, confirmed lineups, news, and sportsbook markets remains unsolved.
- PBP access exists, but naive lineup reconstruction failed truth testing.
- Official GameRotation feasibility timed out and remains unproven.
- Advanced/tracking availability does not establish predictive value.

## Email requirement
Automatic progress-email delivery for journal/handoff updates remains required but is not yet implemented or tested. Do not claim emails are being sent.
