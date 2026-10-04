# NBA_MIKE v2 — Next Agent Handoff

## Project
Research-first NBA prediction and betting-decision platform.

## Root
`C:\Users\micha\Coding\python\nba_mike_v2`

## Environment
Windows / PowerShell / Python / Jupyter / Git / CPU-only.

## Git baseline
P0-S1 committed as `62a5a80`.

## Current phase
P0 — Feasibility & Scientific Design.

## Current milestone
P0-S2 — Target & Data Feasibility.

## Completed
- P0-S1 governance foundation.
- P0-S2 Research Pass 1 source reconnaissance.
- Initial target registry.
- Initial data feasibility matrix.
- AS_OF_TIME / historical reconstruction standard.

## Working research architecture
`Availability -> Minutes -> Role/Opportunity -> Stat Distributions -> Market Probability -> Edge/EV -> Correlation -> Tickets`

This is not yet production-approved.

## Initial core research targets
Availability, minutes, points, rebounds, assists, 3PM.
PRA/PR/PA/RA: compare direct vs joint-component derivation.
Parlay construction remains BLOCKED.

## Important findings
- Core basketball history is much deeper than historical player-prop markets.
- Different data families require different research eras.
- Mutable pregame inputs require timestamped snapshots.
- No single provider is approved as the universal source.
- NBA_MIKE should eventually preserve its own prospective snapshots.

## Unresolved
- practical bulk source for core historical data
- tracking-category historical completeness
- historical injury archive reconstruction
- starter timestamp reconstruction
- FanDuel/DraftKings historical prop coverage
- paid-provider cost/value
- cross-provider canonical IDs

## Exact next task
P0-S2 Research Pass 2:
1. design controlled POC source tests;
2. test representative historical dates;
3. measure schemas, IDs, missingness and timestamps;
4. test AS_OF_TIME reconstruction;
5. make source decisions only after evidence;
6. do not train models.

## Continuation
```powershell
Set-Location "C:\Users\micha\Coding\python\nba_mike_v2"
git status
git log --oneline --decorate -5
```

## P0-S2 CLOSEOUT HANDOFF

Current milestone: P0-S2 complete — PASS WITH EXPLICIT LIMITATIONS.

Decisive finding: for historical game date D, use season-to-date statistical information through D-1 as the initial leakage-safe feature boundary. POC-09 passed this test in 2019-20, 2023-24, and 2025-26: all target-date players gained exactly one GP, with zero wrong target deltas and zero non-target changes.

Do not treat naive PBP rotation reconstruction as authoritative. POC-04 failed strict truth testing. POC-05 proved official starters are available but later period-start inference can be ambiguous. POC-06 GameRotation timed out in all three tests and is not an approved required dependency.

Base and advanced D-1 aggregates are research candidates. Tracking data is optional/advanced until depth, stability, missingness, and predictive value are tested.

Unresolved: intraday injury, confirmed lineup, news, and sportsbook market timestamp reconstruction.

NEXT MILESTONE:
P0-S3 — Canonical Data Architecture & Dataset Contract.

P0-S3 should define raw/intermediate/feature layers, schemas, IDs, provenance, caching, validation, error handling, and reproducible player-game row construction. Do not train models until later Step-0 gates explicitly authorize it.

