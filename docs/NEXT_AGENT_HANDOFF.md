# NBA_MIKE v2 — Next agent handoff

Current phase: P0-S4 S4.1 research hardening; S3 committed at e427c76. S4 original unit and historical research passed (81 tests), but S4 remains uncommitted pending S4.1 validation.

S4.1 replaces opportunity feature builder and research runner. D-1 calendar-date boundary is enforced; duplicate player-dates share historical features. Research outputs are segmented by role change, prior-history depth, and realized minutes (retrospective only). Historical NBA injury/lineup/market evidence remains blocked.

Run S4.1 acceptance, real-data runner, full regression; review JSON and CSV. Commit only after outputs pass and interpretation is documented. Next phase S5 adaptive recent-form windows, not model training.

## S4.1 Research Conclusions — 2026-10-07

- Last-five minutes average led the tested simple baselines in 2019-20, 2023-24, and 2025-26.
- Stable-role last-five MAE: 4.822, 4.908, 4.854.
- Role-change last-five MAE: 5.674, 5.641, 5.721.
- Last-five outperformed last-three in both role groups.
- Role-change flags indicate greater historical prediction uncertainty.
- These are descriptive findings only, not validated betting edges.
- S5 will investigate adaptive windows and chronological robustness.
