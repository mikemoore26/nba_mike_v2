# S8.22.10.6 — Independent schedule reconciliation

## Goal
Reconcile repeated `REVERSED_HOME_AWAY_CONFLICT` flags at the unique game/date level rather than count each player as an independent conflict.

## External corroboration
- https://www.basketball-reference.com/leagues/NBA_2024_games-november.html — historical away/home schedule for Nov 15 and 16, 2023.
- https://www.nba.com/game/cle-vs-por-0022300199 — official NBA confirmation for CLE@POR and game ID 0022300199.

## Safeguards
Read-only input, SHA256 of input ledger, no overwrite of existing crosswalk, no auto-approved manual reviews, no blanket certification of all game IDs. Eight Nov 15 and two Nov 16 matchups explicitly enumerated. Historical publication timing remains NOT_CERTIFIED. **RESEARCH_ONLY / BLOCK_TRAINING**.

## Interpretation
Old crosswalk was likely systematically reversed; independent schedule corroborates injury-report orientation for the listed games. Count mismatches by unique date/matchup and retain previous flags for auditability.
