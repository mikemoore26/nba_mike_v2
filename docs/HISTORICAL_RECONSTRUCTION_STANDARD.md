# NBA_MIKE v2 — Historical Reconstruction Standard

## Status
P0-S3 S8 research/acceptance standard.

## Governing time rule
For a target NBA game date D, the initial statistical reconstruction may use eligible statistical events dated no later than D-1. Same-day earlier-game information is intentionally excluded.

## Reconstruction sample
S8 uses 2019-20, 2023-24, and 2025-26, preserving the season anchors already used in P0-S2 historical cutoff feasibility work.

A target date is selected deterministically from inside each regular season rather than from the season boundary. The exact date is written to the S8 report.

## Required evidence
For every sampled season:
- source retrieval returns player-game evidence;
- canonical minimum identity/date fields are present;
- duplicate `(game_id, player_id)` records are rejected;
- D-1 reconstruction contains no row on or after target date D;
- D rows remain audit outcomes, not predictive inputs;
- target-date players gain exactly one player-game between D-1 and D;
- non-target players gain zero;
- reordering source rows does not alter the logical D-1 snapshot hash.

## Fail-closed behavior
Any failed season makes S8 fail. Network/API failure is an ERROR/FAIL, not permission to substitute fabricated evidence.

## Explicit non-claims
S8 does not prove exact intraday historical availability for:
- injuries;
- confirmed lineups;
- news;
- sportsbook props/odds/line movement;
- ambiguous rotation/stint truth.

Those domains remain quarantined until separately proven.

## Modeling gate
Predictive model training remains prohibited until the P0-S3 closeout explicitly opens the next phase.
