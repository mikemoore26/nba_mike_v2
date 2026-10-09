# S8.10 — Standalone fail-closed predictor contract

Research only. This module is deliberately **not wired** to any training code. It cannot authorize model training.

From project root:

```powershell
python -m pytest -q tests/test_s810_contract.py
python .\research\p0_s8\s8_10\run_s8_10.py --project-root .
```

Outputs: `results/s8_10_report.json`, `results/s8_10_cases.csv`.

`validate_predictors(frame, allowed)` returns only explicitly listed numeric finite features and rejects common outcome, target and ID columns. It does not infer feature lineage or prove a seemingly safe feature was available before tipoff. `validate_chronological_fold(train_dates, test_dates)` rejects same-day and overlapping folds; it does not fit preprocessing. `assert_research_only()` always blocks training.

Do not approve training or connect the contract to model fit until independent as-of, eligibility, calendar, downstream-column, and fold-local preprocessing gates are satisfied.
