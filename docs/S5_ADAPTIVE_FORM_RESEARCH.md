# P0-S4 S5 — Adaptive recent-form window research

**Status: RESEARCH_ONLY.** Candidate windows 2, 3, 4, 5, 6, 8, 10, 15, season-to-date, exponentially weighted means (spans 3, 5, 10). These are **minutes** candidates, not trained statistical models.

The S4 last-five average is the benchmark. Evaluation uses chronological prequential predictions, with a 30-date warmup, at least five prior dates per player, and a pooled adaptive selector requiring 100 previously observed errors per candidate. A whole day's results enter history only after all predictions for that day have been produced. This prevents same-day target leakage.

**Important:** This is a global selector, not personalized player-specific adaptation. Per-season exploratory comparison and selector design are not a locked out-of-sample final holdout. No promotion on a small MAE advantage. Compare subgroup sample sizes, role changes and uncertainty; require later multi-season temporal replication and confidence intervals. No odds or profitability claims.

Data fetched live through existing S4 source; immutable provenance remains outstanding. A player's multiple games on the same date are aggregated to one historical date for rolling windows. Zero-history and DNP coverage are not solved. Do not interpret realized-minutes groups as live features.

Run `python research/p0_s4/s5/run_s5_acceptance.py`, then `python research/p0_s4/s5/run_s5.py`, then `python -m pytest -q`. Outputs are `research/p0_s4/s5/results/s5_report.json` and `s5_candidates.csv`.
