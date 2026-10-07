# S6.3 — Error Attribution and Calibration Stability

## Purpose
Diagnose existing S6.2 forecasts and uncertainty intervals; **do not train another model**.

## Design
- Same player-games for all three S6.2 methods; duplicate and mismatch checks.
- Coverage, mean interval width, MAE, error >10/>15 minutes.
- Subgroups: role stability, history depth, prior-error volatility, calendar month, thirds of observed season.
- Paired differences vs role-specific baseline, with 500 deterministic calendar-date bootstrap replicates. Each resample retains all players on sampled dates.
- Descriptive flag when coverage <88% for groups with >=100 rows. These are screening thresholds, not calibrated statistical tests.

## Interpretation
- A narrower interval is not necessarily better if it misses more actual outcomes.
- Bootstrap CIs are descriptive and may be unstable across seasons.
- Do not tune models to 2025-26 results and then call that season untouched validation.
- Forecast MAE is identical across interval methods by construction; intervals cannot correct point predictions.
- No injury/DNP/lineup/market information in this step.

## Advancement gate
After reviewing all three seasons, decide whether S6.1 role-specific remains the best baseline and identify the next *data* improvement (e.g., pregame availability/lineup signals). No betting deployment.
