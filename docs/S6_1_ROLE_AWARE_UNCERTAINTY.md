# S6.1 Role-Aware Minutes Uncertainty — Research Protocol

## Motivation
S6 90% nominal intervals covered approximately 89% overall but only 84–85% of role-change player-games. Compare pooled, role-specific, and partially pooled (shrinkage) interval calibration on exactly matched predictions.

## Methods
The baseline remains EWM-5. Input comes from S6 prediction CSVs, not freshly fetched data. Each season is evaluated in calendar order. On each date, radii are calculated using strictly earlier date residuals; outcomes are appended only after that date's forecasts. At least 30 prior evaluation dates and 100 pooled errors are required. A subgroup-specific empirical quantile is available only after 100 group errors; otherwise the method falls back to pooled. Shrinkage weight is `n_group/(n_group+250)` for sufficiently populated groups. Interval bounds are clipped to [0,60] minutes. The pooled empirical quantile uses ceil((n+1)*(1-alpha)).

## Decisions and caveats
Compare empirical coverage AND width overall and by role. Do not select a winner based on coverage alone. Same-season historical selection and the already inspected 2025–26 season are not pristine prospective validation. Residual distributions are nonexchangeable under lineup, injury, rotation, and coaching changes. These intervals are exploratory, not guaranteed conditional coverage. Do not promote a production model or betting edge based on this study.

## Reproducibility
`python research/p0_s4/s6_1/run_s6_1_acceptance.py`
`python research/p0_s4/s6_1/run_s6_1.py`
`python -m pytest -q`
Output: `research/p0_s4/s6_1/results/s6_1_report.json`.
