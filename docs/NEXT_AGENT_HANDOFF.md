# NBA_MIKE v2 — NEXT AGENT HANDOFF

## Current state

Project: `nba_mike_v2`

Environment:
- Windows
- PowerShell
- Python virtual environment `.venv`
- CPU-only design
- Git on `main`

Last confirmed user Git checkpoint before S4:
- `3eb7a28 Complete P0-S3 S3 canonical identity system`

## Completed architecture milestones

- P0-S3 S1 — Canonical Data Architecture
- P0-S3 S2 — Storage & Manifest Standard
- P0-S3 S3 — Canonical Identity System
- P0-S3 S4 — Schema Validation & Provenance Enforcement package prepared; must be run and committed on the user's machine before calling it complete.

## S4 implementation

New standard:
- `docs/SCHEMA_VALIDATION_STANDARD.md`

New code:
- `src/nba_mike/validation/__init__.py`
- `src/nba_mike/validation/schema.py`
- `src/nba_mike/validation/provenance.py`

Tests:
- `tests/test_schema_validation.py`

Acceptance:
- `research/p0_s3/s4/run_s4_acceptance.py`

Core behavior:
- explicit required-column/type/null/value contracts;
- primary-key duplicate detection;
- schema-drift detection;
- fail-closed validation;
- non-PASS parent blocking;
- SHA-256 parent verification/tamper rejection.

## Required continuation discipline

1. Run S4 tests and acceptance on the user's machine.
2. Inspect `git status`.
3. Commit only after PASS.
4. Keep `docs/DEVELOPMENT_JOURNAL.md` updated at every material milestone.
5. Keep this handoff file updated/replaced so another AI can resume without reconstructing project state.
6. Keep Git checkpoints at stable milestones.
7. Do not train predictive models until the governance/milestone plan explicitly opens that gate.
8. Do not weaken validation thresholds merely to force PASS.

## Email requirement

The user wants automatic progress emails when the development journal and AI handoff are updated, with the updated files attached. That email subsystem has NOT yet been implemented in NBA_MIKE v2. Do not claim emails are being sent. Preserve this as an explicit project requirement until implemented and tested.

## Research constraints still active

- D-1 is the conservative reproducible statistical pregame boundary established by P0-S2.
- Exact intraday historical truth for injuries, confirmed lineups, news, and sportsbook markets remains unsolved unless later evidence proves otherwise.
- PBP access exists, but naive lineup reconstruction failed truth testing.
- Official GameRotation feasibility encountered timeouts and was not proven.
- Availability of advanced/tracking data does not prove predictive value.
