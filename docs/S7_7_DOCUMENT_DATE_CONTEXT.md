# S7.7 — Document-level date context (research only)

## Goal
Fill missing game dates when the entire parsed report contains exactly one explicit date and a target row has an explicit matchup. This is a **heuristic**, not independently verified ground truth.

## Safety gates
- No date backfill when multiple distinct explicit dates are found.
- No backfill on rows without a matchup.
- Never carry team, player, matchup, or injury reason across page boundaries.
- Every backfilled date is marked `DOCUMENT_UNIQUE_DATE_INFERRED` and `DATE_INFERRED_REVIEW_REQUIRED`.
- Rows with inherited layout remain review-required.
- Training and historical publication gates remain closed.

## Commands
`python research/p0_s4/s7_7/run_s7_7_acceptance.py`
`python research/p0_s4/s7_7/run_s7_7.py --pdf PATH --url OFFICIAL_URL`

## Evaluation
Compare `rows_with_date`, `date_inferred_rows`, `layout_complete_records`, per-page counts, and flags against S7.6. Counts are not accuracy metrics. Investigate orphan continuations separately.
