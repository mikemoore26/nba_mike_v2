# S8.11 — Contract integration feasibility

Research only. No network, fitting, production modification, or approval.

Run from project root:

```powershell
python -m pytest -q tests/test_s811_integration_feasibility.py
python .\research\p0_s8\s8_11\run_s8_11.py --project-root .
```

Requires S8.10 contract and existing opportunity/adaptive-form builders. Outputs `results/s8_11_report.json`, `s8_11_cases.csv`, `s8_11_entrypoints.csv`. Synthetic examples intentionally do not certify any feature for training.
