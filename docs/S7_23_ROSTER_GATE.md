# S7.23 — independent roster evidence contract

## Objective
Verify player/team assignment independently of the injury report extraction pipeline. Do not use NBA injury report section events as roster evidence.

## Evidence sourcing
Prioritize date-specific NBA transaction/roster records with stable player IDs and verifiable publication dates; evaluate `nba_api`/NBA stats roster endpoints for coverage, timestamp provenance and rate limits, and a second independent source where available. No source is preapproved; collect and inspect evidence before loading. Avoid current rosters as substitutes for March 2026 rosters. Never invent roster membership.

## Classification
`VERIFIED` means supplied independent evidence has the matching team and date range and no contradictory row. `CONFLICT` means contradictory evidence. `UNRESOLVED` means missing, stale, ambiguous, or ineligible evidence. Current name matching is provisional, not proof of stable identity. No automatic promotion to training. All 475 existing candidates remain research-only until publication and cutoff checks pass independently.

## Future improvement
Build an acquisition adapter that snapshots source bytes, SHA256, HTTP retrieval time and original source-as-of time, validates player IDs and transaction boundaries, and produces dated roster intervals. Add adversarial tests for trades, waived players, two-way assignments, name collisions and source revisions.
