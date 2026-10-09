# S7.47 — Offline archived claim inspection

Run `python research/p0_s4/s7_47/run_s7_47.py` after S7.46 `--fetch-captures`. Optionally pass `--cutoff 2026-02-06T00:00:00Z` for a *specified* historical cutoff; no default is inferred. Outputs `results/s7_47_review.csv` and `results/s7_47_report.json`. The runner does not use the network or authorize training. Keep captured HTML and generated CSV untracked.
