# S6.3 — Error attribution and stability

Offline-only diagnostics from `research/p0_s4/s6_2/results/s6_2_predictions_<season>.csv`.

From project root:

```powershell
python research/p0_s4/s6_3/run_s6_3_acceptance.py
python research/p0_s4/s6_3/run_s6_3.py
python -m pytest -q
```

Report: `research/p0_s4/s6_3/results/s6_3_report.json`.

No production promotion. Do not use previously inspected 2025-26 as untouched validation.
