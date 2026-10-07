# P0-S3 S8 — Historical Reconstruction Sample

## Purpose
Exercise the leakage-safe historical reconstruction boundary on real NBA player-game logs across the same three season anchors used during P0-S2 feasibility work:

- 2019-20
- 2023-24
- 2025-26

For each season, the runner deterministically chooses an internal regular-season target date and verifies:

1. source player-game rows can be normalized into the minimum canonical identity/date shape;
2. the reconstructed statistical state for target date D contains only rows dated before D (D-1 or earlier);
3. players who play on D gain exactly one row when comparing through D-1 versus through D;
4. players who do not play on D gain zero rows;
5. rebuilding from differently ordered source rows produces the same logical snapshot hash.

## Important boundary
Target-date rows are used only as audit labels/evidence. They are never inserted into the D-1 predictive state.

This milestone does NOT solve exact intraday historical truth for injuries, confirmed lineups, news, sportsbook props/odds/line movement, or ambiguous rotation/stint reconstruction.

No predictive model training is permitted in S8.
