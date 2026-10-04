# NBA_MIKE v2 — NEXT AGENT HANDOFF

## Current state
Project: `nba_mike_v2`
Environment: Windows / PowerShell / Python `.venv` / CPU-only / Git `main`.

## Confirmed checkpoints
- `b2d958f` — P0-S3 S1 canonical data architecture
- `2a7d4ed` — P0-S3 S2 storage and manifest standard
- `3eb7a28` — P0-S3 S3 canonical identity system
- `8776dbb` — P0-S3 S4 schema validation and provenance enforcement

## P0-S3 S5
Package: Canonical Dataset Builder & Raw -> Validated -> Canonical Pipeline.
S5 must be run and committed on the user's machine before being called complete.

New standard: `docs/CANONICAL_BUILD_STANDARD.md`
New code: `src/nba_mike/canonical/builder.py`
Tests: `tests/test_canonical_builder.py`
Acceptance: `research/p0_s3/s5/run_s5_acceptance.py`

S5 behavior: verify PASS parent + SHA-256; enforce source schema; resolve canonical identities; reject unresolved/ambiguous identity, duplicates, and impossible values; write a new canonical player-game artifact; record parent-linked provenance.

## Required continuation discipline
1. Run S5 tests and acceptance.
2. Inspect `git status`.
3. Commit only after PASS.
4. Keep Development Journal and this handoff current.
5. Do not weaken validation to force PASS.
6. Do not train predictive models until the milestone plan explicitly opens that gate.

## Email requirement
Automatic progress email for journal/handoff updates remains required but is not yet implemented or tested. Do not claim emails are being sent.

## Research constraints
D-1 remains the conservative reproducible statistical pregame boundary. Exact intraday historical truth for injuries, confirmed lineups, news, and sportsbook markets remains unsolved. Naive PBP lineup reconstruction failed truth testing; GameRotation was not proven because of timeouts. Advanced/tracking availability does not prove predictive value.

## Proposed next milestone after S5
P0-S3 S6 should expand canonical construction into reproducible D-1 snapshot building / point-in-time dataset assembly, subject to the milestone plan and S5 results. Do not skip S5 acceptance.
