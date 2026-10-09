# S8.4 — Official NBA schedule crosscheck

## Goal
Independently test S8.3's 88 plausible 2019–20 restart game IDs against NBA Stats `leaguegamefinder` team-game rows and compare `GAME_ID` + `GAME_DATE`. Direct HTTPS retrieval from `stats.nba.com` is the only path to `OFFICIAL_GAME_ID_DATE_MATCH`. Two team rows with the same date count as one game; contradictory dates are blocked. Network failure, absent IDs, malformed response and mismatched dates remain visible blockers.

## Evidence boundaries
NBA Stats live historical API is an official NBA-operated source for historical game date and ID. It is **not** proof of when the source data was first published, pre-tipoff features, roster history, or betting-market odds. Offline JSON is an unattested diagnostic and cannot mark games verified. The API can be inaccessible; this must not be worked around by invented results.

## Outputs and governance
JSON report, per-game CSV, raw official response when fetched, source URL, retrieval UTC, SHA-256, and explicit failure reason. Input game logs untouched. `RESEARCH_ONLY / BLOCK_TRAINING`; historical roster and transaction features remain blocked under S7.51.
