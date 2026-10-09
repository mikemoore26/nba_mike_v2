# S8.20 — Hybrid historical/forward strategy (design only)

Run from the repository root:

```powershell
python -m pytest -q tests/test_s820_strategy.py
python .\research\p0_s8\s8_20\run_s8_20.py --project-root .
```

Results (not committed): `results/s8_20_report.json`, `s8_20_strategy_comparison.csv`, `s8_20_capture_design.csv`, `s8_20_checkpoint_design.csv`, `s8_20_prior_evidence.csv`.

No network requests, future captures, scheduled jobs, training, certification, or betting are performed. This milestone is a **design decision**, not a data ingestion implementation. All historical snapshots remain exploratory. Do not represent an actual capture as pregame-available unless it was collected before tipoff and its provenance independently reviewed. Keep `RESEARCH_ONLY / BLOCK_TRAINING`.
