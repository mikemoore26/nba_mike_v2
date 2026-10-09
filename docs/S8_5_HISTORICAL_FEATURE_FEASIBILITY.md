# S8.5 — Historical Feature Feasibility Decision

## Why this pivot

S8.4 failed to retrieve the NBA Stats official schedule (timeout); all 88 restart games remain unverified. Repeated calls to the same endpoint without a new access method have low expected yield. Preserve the calendar blocker, do not invent verification, and redirect to testable offline feature-lineage questions.

## Scope

Audit three S5.1 game-log snapshots for strict prior-date player-history feasibility, invalid values, duplicate player-games, game-date conflicts and same-day ambiguity. Source files remain untouched. Historical publication timing and player pregame availability are not attested.

## Governance

`RESEARCH_ONLY / BLOCK_TRAINING` remains mandatory. Prior-game averages are **demonstrations**, not certified pre-tipoff model features. Same-game outcomes are forbidden inputs. Roster, injury, market and calendar chronology gates remain independent blockers. Next stage should examine the actual existing S5/S6 feature builders for timestamp lineage and sample selection, not start training.
