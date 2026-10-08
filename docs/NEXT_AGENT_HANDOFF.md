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

## Current milestone: P0-S4 S5
S4/S4.1 baseline was last-five minutes MAE ~5; role-change subgroup has higher error. S5 patch adds `features/adaptive_form.py`, tests, research runner and standard. S5 is RESEARCH_ONLY and uncommitted until local tests and historical results reviewed. Next: inspect candidate scores and prequential last-five vs adaptive MAE, plus role subgroup and selected counts. Preserve no-leakage rules and closed model-training gate.


## S5.1 pending validation
Install research/p0_s4/s5_1, docs/S5_1_ROBUSTNESS_STANDARD.md, tests/test_s5_1_robustness.py. Run acceptance, runner, full pytest; inspect report and manifest. EWM-5 was selected after earlier inspection of 2025-26, so the 2025-26 split is a retrospective chronological check, not a truly untouched holdout. S5 remains RESEARCH_ONLY. No commit until review.

## S6 handoff (pending execution)
New `src/nba_mike/features/minutes_uncertainty.py`, S6 runner and tests.
Run acceptance, offline snapshot-backed research and full regression. Review
coverage and width; do not promote predictive intervals without additional validation.


## S6 Research Conclusions — 2026-10-07

- Full regression: 100 tests passed.
- Overall 90% interval coverage: 88.9%-89.3%.
- Stable-role coverage: 89.8%-90.2%.
- Role-change coverage: 84.4%-85.3%.
- Mean interval width: approximately 19.7 minutes.
- Role-change undercoverage is consistent across three seasons.
- Pooled calibration is insufficient for reliable subgroup coverage.
- S6 remains RESEARCH_ONLY; no betting promotion.
- Next: S6.1 role-aware uncertainty calibration.

## S6.1 handoff — pending local evaluation
New `src/nba_mike/features/role_aware_uncertainty.py`, `tests/test_role_aware_uncertainty.py`, `research/p0_s4/s6_1/` runner, and `docs/S6_1_ROLE_AWARE_UNCERTAINTY.md`. Requires S6 prediction CSVs. Compare matched-role coverage and interval width, verify 105 total tests if prior 100 pass, then decide on research-only checkpoint. Do not claim production or betting readiness.


## S6.1 Research Conclusions — 2026-10-07

- Full regression: 105 tests passed.
- Role-specific calibration improved role-change coverage toward 90%.
- Shrinkage achieved near-target coverage with slightly narrower intervals.
- Role-specific calibration increased interval width for changing-role players.
- Methods compared on the same S6.1 evaluation rows.
- S6.1 remains RESEARCH_ONLY.
- Next: S6.2 conditional uncertainty and chronological validation.

## S6.2 pending evaluation
New `conditional_uncertainty.py`, S6.2 runner, tests and documentation. Run acceptance, offline report and full suite. Review common-sample coverage/width for role/history/volatility and existing S6.1 baselines. Preserve RESEARCH_ONLY until independent chronological validation.


## S6.2 Research Conclusions — 2026-10-07

- Acceptance passed.
- Full regression: 110 tests passed.
- Conditional uncertainty evaluated on common S6.1 player-games.
- History and volatility improve risk differentiation.
- Role-change coverage does not consistently improve over role-specific calibration.
- 2025-26 volatility-aware coverage: 89.14%; mean width: 19.64 minutes.
- Role-specific baseline coverage: 89.54%; mean width: 20.15 minutes.
- Retain role-specific as reference baseline.
- S6.2 remains RESEARCH_ONLY.
- Next: S6.3 error attribution and calibration stability.
## S6.3 handoff
- Module: `src/nba_mike/evaluation/s6_3_diagnostics.py`.
- Runner: `research/p0_s4/s6_3/run_s6_3.py` (offline S6.2 outputs).
- Acceptance: `research/p0_s4/s6_3/run_s6_3_acceptance.py`.
- Report: `research/p0_s4/s6_3/results/s6_3_report.json`.
- No production promotion. Await report, regression tests, Git review and commit.


## S7.0 handoff (pending local execution)
- Prior: S6.3 retrospective error attribution, role-specific minutes uncertainty baseline; no production promotion.
- Current: offline S7.0 provenance validator and local research inventory; `research/p0_s4/s7_0/results/s7_0_feasibility_report.json` after runner.
- No historical injury/lineup source verified; no network data acquisition; no betting models authorized.
- Next: source-backed timestamped sample, define prediction cutoff and DNP player-game universe, then S7.1 leakage-safe join POC.

