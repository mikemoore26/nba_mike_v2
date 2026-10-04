# P0-S2 POC-06 — Official GameRotation/Stint Feasibility Truth Test

POC-05 showed that substitution constraints can uniquely solve many period starts,
but some periods remain fundamentally ambiguous.

POC-06 tests the NBA Stats `GameRotation` endpoint as a stronger source.

The endpoint exposes team/player stint rows including:

- `PERSON_ID`
- `TEAM_ID`
- `IN_TIME_REAL`
- `OUT_TIME_REAL`
- `PLAYER_PTS`
- `PT_DIFF`
- `USG_PCT`

## Truth tests

For representative games from 2025-26, 2023-24, and 2019-20:

1. request GameRotation;
2. inspect schema/nulls/duplicates;
3. empirically determine the time-unit scale by comparison with official minutes;
4. derive each player's minutes from rotation stints;
5. compare against the official traditional box score;
6. test whether every interval contains exactly five active players per team.

Strict minute tolerance: maximum absolute player error <= 0.25 minutes.

## Important

A successful three-game POC does NOT make GameRotation production-ready.
It only justifies broader sampled validation.

If the endpoint is unavailable for an era, that is a feasibility result. Do not
silently substitute a weaker source.
