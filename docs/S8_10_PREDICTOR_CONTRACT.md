# S8.10 — Predictor and chronological fold contract

## Motivation
S8.9 inspected 131 files and surfaced 45 source-review candidates, including 2 predictor-selection patterns in the opportunity feature builder. It did not identify or certify an actual training matrix. S8.8's 14 synthetic tests passed, but downstream use is unverified.

## Scope
- New standalone contract under `research/p0_s8/s8_10/` (no edits to existing `src/nba_mike`).
- Explicit predictor allowlist; reject missing, duplicate, normalized-collision, nonnumeric, boolean, NaN and infinite columns.
- Reject known same-game outcome aliases, `target_*`, `actual_*`, `realized_*`, identifiers and label-like names.
- Date-separated train/test boundary checks (including same-day overlap).
- Always-failing training authorization guard.
- Synthetic self-check report and unit tests.

## Limits / next actions
A syntactically safe feature can still leak through its values, joins, publication timing, or a future model's behavior. Date separation does not establish fold-local scaling, imputation, tuning or calibration. This patch is not integrated with model training. Next, obtain the exact downstream matrix-construction source, verify its columns and fold-local fit operations, then decide whether to integrate these checks. Independently resolve pregame player eligibility/DNP, historical publication timestamps and the 88 restart calendar games.

Decision: `RESEARCH_ONLY / BLOCK_TRAINING`.
