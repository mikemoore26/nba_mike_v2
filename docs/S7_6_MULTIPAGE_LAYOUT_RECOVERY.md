# S7.6 — Multi-page layout recovery (research-only)

Replaces `src/nba_mike/data/injury_layout.py` (S7.5) with a compatible parser. Pages lacking a header reuse the last detected column positions only when page widths agree within 2 points. **Team, matchup, date, and player context are never inherited across page boundaries.** Reused columns mark all recovered records `REVIEW_REQUIRED` with `INHERITED_COLUMN_LAYOUT_UNVERIFIED`. No training authorization.

The per-page diagnostic reports header mode, recovered record count, complete records, and review-required records. A count increase is not evidence of accuracy. Compare source PDF samples, especially first rows on pages 2–8, and test wrong-team/wrapped-reason cases before promoting extraction quality.

Run `python research/p0_s4/s7_6/run_s7_6_acceptance.py`, `python -m pytest -q`, then `python research/p0_s4/s7_6/run_s7_6.py --pdf <PDF> --url <OFFICIAL_URL>`. Outputs in `research/p0_s4/s7_6/results/`.

S7.5's existing runner imports the same module; S7.6 is a replacement implementation, not an independent parallel parser. Historical publication timing remains unverified.
