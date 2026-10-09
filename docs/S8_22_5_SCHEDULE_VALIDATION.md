# S8.22.5 — Provider schedule validation and coverage gate

## Starting evidence

S8.22.4 live request for 2026-10-10 returned HTTP 200, successful raw S8.21 capture, `parse_status=PASS`, and zero game records. That proves connectivity and response parsing, **not** complete schedule coverage. Provider IDs, tipoff accuracy, permissions, and player eligibility remain unverified.

## New rules

1. Empty provider rows => `EMPTY_SCHEDULE_UNVERIFIED` unless independent reference shows games, then `EMPTY_SCHEDULE_CONTRADICTED_BY_REFERENCE`.
2. Populated provider rows without independent reference => `PROVIDER_GAMES_PRESENT_UNVERIFIED`.
3. Independent reference and team-ID crosswalk are supplied as separate offline files with provenance; crosswalk IDs are never guessed.
4. Exact game-date and home/away team match produces only a candidate official game ID. UTC tipoff comparison uses a five-minute tolerance; missing or ambiguous timestamps remain unverified.
5. Incomplete/mismatched counts => `PARTIAL_OR_UNVERIFIED_COVERAGE`; even a perfect single-date comparison => `CANDIDATE_DATE_COVERAGE_MATCH_REQUIRES_REVIEW`.
6. No promotion to trusted, no automatic schedule polling, no model training, no changes to S8.21 ledger or S8.22.4 adapter.

## Remaining gates

Independently confirm official schedule provenance, provider licensing/entitlement, crosswalk, preseason coverage, time zones and tipoff updates, multiple representative dates, forward checkpoints, and as-of player eligibility. A single historical-date success cannot certify prospective capture.
