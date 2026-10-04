# P0-S2 POC-09 — Game-Level Historical Reconstruction & Leakage Boundary

POC-08 proved that NBA Stats honors historical `DateTo` cutoffs.

POC-09 now tests the concrete training-row rule:

> For a game on date **D**, build season-to-date statistical features using a
> cutoff of **D-1**, then use the player game log on **D** only as the outcome.

This is deliberately conservative. It prevents a historical row from seeing
the target game's own statistics.

The test compares GP before and through the target date. Every player who
played on the target date should gain exactly one game; players who did not
play that date should not change.

Advanced and tracking data are also probed at the D-1 cutoff.

A PASS does not solve intraday injury, lineup, news, or market timing.
