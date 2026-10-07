# S5.1 — EWM robustness and retrospective chronological confirmation

Training seasons: 2019-20 and 2023-24. Evaluation season: 2025-26. The training set selects one global candidate using MAE. EWM-5 is also assessed as a *pre-declared research comparator*, alongside the original last-five baseline. Equal holdout rows, prior-date-only features, date-block bootstrapped paired MAE differences (2,000 draws, seed 517). Positive gain favors EWM-5.

**Critical scientific caveat:** the user and project already inspected 2025-26 S5 results and selected EWM-5 as a promising candidate. Therefore **2025-26 is not genuinely untouched**. This step tests chronological separation in the code and performs a retrospective robustness check; it cannot provide a new blind holdout or justify promotion to production. A future genuinely unexamined season/period is required for that gate.

Snapshots: on first run, player game logs for each season are saved to `research/p0_s4/s5_1/snapshots/`, with SHA-256 manifest in `results/`. Run `--offline` thereafter. The original S5 runs were fetched live and cannot be retroactively proven identical to these new snapshots. Preserve these files, and review whether to commit their hashes vs raw CSV under your data retention policy. The script will not overwrite existing snapshots.

Outputs: `results/s5_1_report.json`, `results/s5_1_manifest.json`. No injury, DNP, confirmed lineup, or odds data are incorporated. No betting promotion.
