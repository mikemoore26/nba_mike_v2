# P0-S4 S6 — Minutes uncertainty research
Baseline: existing D-1 EWM-5 forecast. Intervals use an expanding pool of absolute
historical errors, updated only after all predictions for the same date are evaluated.
The empirical conformal-style quantile uses ceil((n+1)*(1-alpha)) and clips intervals
to physically plausible [0,60] minutes. This is an exploratory sequential method,
**not a guarantee of conditional or exact finite-sample coverage** under NBA drift.

The report includes empirical coverage, average interval width, MAE, and fractions
with errors >5, >10 and >15 minutes. Role-change segmentation is descriptive.
Calibrations are season-local; S5.1 snapshot hashes must match the manifest.
No historical injury, DNP, lineup, market, or player-specific calibration is claimed.
This milestone does not authorize a model or betting promotion.
