# S6.2 — Conditional uncertainty (RESEARCH ONLY)

## Question
Can past error volatility and prior history depth help distinguish minutes uncertainty beyond the role-change flag?

## Predeclared comparisons
1. S6.1 pooled and shrinkage baselines.
2. Role-specific calibration.
3. Role + history-depth calibration (5–9, 10–19, 20+ prior dates).
4. Role + history-depth + volatility tier. Volatility tier is `high` if mean of the player's last up to eight **prior-date forecast absolute errors** exceeds five minutes; `low` otherwise, and `unknown` with fewer than three prior residuals.

All quantiles are derived from outcomes on strictly earlier dates; same-date outcomes enter history only after that date. Sparse cells fall back to role+history then role then pooled quantiles (minimum 100 calibration errors per cell by default). Research calibration resets each season. Output comparison uses the intersection of S6.1 eligible player-games.

## Readout and gates
Compare coverage against 90% and average interval width, overall and by role, history and volatility. A wider interval that increases coverage is not necessarily a better conditional model. Do not choose hyperparameters by repeatedly inspecting 2025–26. No claim of conditional coverage, untouched holdout, injury-aware predictions or betting edge.

## Known limitations
This volatility proxy measures historical *forecast error*, not raw minutes variance. It requires outcomes from earlier games and may react slowly to newly changed roles. Role flag and EWM forecast inherit upstream S4/S5 limitations. The 2025–26 season has already been examined; future independent validation is required.
