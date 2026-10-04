# NBA_MIKE v2 — NEXT AGENT HANDOFF

## Current state
Project: `nba_mike_v2`
Environment: Windows / PowerShell / Python `.venv` / CPU-only / Git `main`

Last confirmed Git checkpoint before S6:
- `48c40b2 Complete P0-S3 S5 canonical dataset builder`

## Completed milestones
- P0-S3 S1 — Canonical Data Architecture
- P0-S3 S2 — Storage & Manifest Standard
- P0-S3 S3 — Canonical Identity System
- P0-S3 S4 — Schema Validation & Provenance Enforcement
- P0-S3 S5 — Canonical Dataset Builder
- P0-S3 S6 — Reproducible D-1 Point-in-Time Snapshot package prepared; run tests/acceptance and commit before calling complete.

## S6 implementation
Standard:
- `docs/POINT_IN_TIME_SNAPSHOT_STANDARD.md`

Code:
- `src/nba_mike/snapshots/__init__.py`
- `src/nba_mike/snapshots/builder.py`

Tests:
- `tests/test_point_in_time_snapshot.py`

Acceptance:
- `research/p0_s3/s6/run_s6_acceptance.py`

## Core S6 rules
- Game D statistical snapshots use only events through D-1.
- Same-day and future statistical rows are excluded.
- Parent must be PASS and SHA-256 verified.
- Duplicate canonical player-game keys fail closed.
- Snapshot logical content is deterministic.
- Zero-history players are explicit; no history is invented.
- Intraday injuries, lineups, news, and sportsbook markets are outside this D-1 statistical safety claim.

## Continuation discipline
1. Run S6 tests and acceptance.
2. Inspect git status.
3. Commit only after PASS.
4. Update development journal and this handoff at every material milestone.
5. Do not weaken gates to force PASS.
6. Do not train predictive models until the governance plan explicitly opens that gate.

## Unresolved research constraints
- Exact intraday historical truth for injuries, confirmed lineups, news, and sportsbook markets remains unsolved.
- PBP access exists, but naive lineup reconstruction failed truth testing.
- Official GameRotation feasibility timed out and remains unproven.
- Advanced/tracking availability does not establish predictive value.

## Email requirement
Automatic progress-email delivery for journal/handoff updates remains required but is not yet implemented or tested. Do not claim emails are being sent.
