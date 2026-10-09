# S8.3 Historical Calendar Validation

## Objective

Resolve the S8.2 2019–20 broad-season date flags without deleting legitimate pandemic-era games or silently certifying dates.

## Method

Read three immutable snapshots; enumerate date/game pairs and count player rows, classify 2019–20 dates on or after July 1 as plausible 2020 restart (July 30–August 14), pre-restart July, or outside research window; detect game IDs assigned to multiple dates and duplicate player-game keys. Compare observed July+ player rows to the S8.2 total of 1,892. Record SHA-256 for each snapshot. Preserve 2023–24 and 2025–26 inventory for regression.

## Gates

The date window is contextual and is **not independent official game-ID/date verification**. S8.4 should obtain independently verifiable official game-level schedule data, join by game ID, and document disagreements before any date certification. Even then, the pre-tipoff feature-provenance and chronology gates are separate and still blocked.

## Governance

`RESEARCH_ONLY / BLOCK_TRAINING`; S7.51 roster/transaction evidence remains blocked. No modeling, market, injury, or betting promotion.
