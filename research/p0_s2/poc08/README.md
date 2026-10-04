# P0-S2 POC-08 — Historical Cutoff / AS_OF_TIME Feasibility

## Why this exists

POC-07 proved that base, advanced, and several tracking data families are
available at season level across the tested eras.

That does **not** prove they are safe historical features.

POC-08 asks the next question: can the NBA Stats endpoints be queried with a
historical `DateTo` cutoff so a simulated prediction does not accidentally see
games that happened later in the same season?

## Test

For each representative season:

1. request BASE stats through an early cutoff;
2. request BASE stats through a later cutoff;
3. compare matched players;
4. require GP to never decrease and to increase for at least some players;
5. require aggregate values to change for at least some players;
6. probe ADVANCED and tracking families at the early historical cutoff.

## Important limitation

A PASS establishes **day-level historical cutoff responsiveness**.

It does not establish exact intraday publication timestamps. Injury reports,
confirmed lineups, odds, line movement, and news still require separate
timestamp-aware feasibility work.
