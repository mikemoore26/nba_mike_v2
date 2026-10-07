# S4.1 — Research hardening

The initial S4 findings were descriptive. This patch addresses calendar-date leakage, adds segmentation and preserves the original report.

**Date contract:** a target date can only use games on strictly earlier dates. Same-day player games share the same pregame history. For exceptionally duplicated player-dates, historical daily outcomes are averaged; the resulting rolling window counts *prior dates*, not exact prior games. These rare cases must be audited before a production game-count feature is approved.

**Reports:** new `s4_1_opportunity_research.json` and `s4_1_opportunity_groups.csv`, alongside the original S4 report. Groups include stable vs flagged role change, realized minutes buckets, and prior-history buckets.

**Interpretation cautions:** Realized-minutes buckets are retrospective diagnostics and cannot be used as live pregame segmentation. Role-change threshold (6 minutes) is a heuristic. No injuries/lineups/market truth is assumed. No model promotion or profitability claim follows from MAE alone.

**Acceptance:** run the S4.1 acceptance script, historical research, then full regression. Review group sizes and method-level errors before S5.
