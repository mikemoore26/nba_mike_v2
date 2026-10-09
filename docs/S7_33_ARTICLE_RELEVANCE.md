# S7.33 — Article relevance and duplicate audit

## Objective
Diagnose S7.32's 24 capture rows but only 2 unique articles; investigate 71 missing-origin rows versus 63 eligible acquisition candidates.

## Design
Offline, content-addressed SHA-256 validation, visible-text parsing (scripts/styles excluded), exact whole-name matching, nearby transaction vocabulary, nearby team mentions for manual inspection, URL reuse statistics, explicit eligibility decomposition. No source claims are promoted. A name near a trade term is a **lead**, not evidence that the named player was traded. Dates and historical publication remain unverified.

## Outputs
`research/p0_s4/s7_33/results/s7_33_report.json` and `s7_33_review.csv` (not committed). Audit flags should guide future discovery improvements, not support as-of training.
