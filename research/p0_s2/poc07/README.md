# P0-S2 POC-07 — Advanced Stats & Opportunity Data Feasibility

## Goal

Determine which player-stat families are realistically available across multiple
NBA eras before NBA_MIKE v2 designs its feature architecture.

This is intentionally **not model training**.

## Probes

### Base player stats
Checks fields such as:

- MIN
- FGA / FG3A / FTA
- OREB / DREB / REB
- AST
- TOV
- PTS

### Advanced player stats
Checks fields such as:

- OFF_RATING / DEF_RATING / NET_RATING
- AST_PCT
- rebound percentages
- EFG_PCT / TS_PCT
- USG_PCT
- PACE
- PIE

### Tracking/opportunity families
Probes:

- Possessions
- Passing
- Drives
- PaintTouch

These are intentionally treated as optional until historical coverage and
reliability are proven.

## Important limitation

This POC tests endpoint access and season-level schema/coverage.

It does **not** prove that a field can yet be reconstructed correctly at a
historical prediction `AS_OF_TIME`. That is a later gate.

## Failure policy

Timeouts, missing fields, empty results, and endpoint errors are findings.
Do not weaken the test or silently substitute another source merely to force PASS.
