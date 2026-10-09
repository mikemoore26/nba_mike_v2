# S8.9 — Downstream predictor leakage audit

Offline read-only reconnaissance of Python source under `src/nba_mike` and `research/p0_s4`.

```powershell
python -m pytest -q tests/test_s89_downstream.py
python research/p0_s8/s8_9/run_s8_9.py --project-root .
```

Outputs (untracked): `results/s8_9_report.json`, `results/s8_9_findings.csv`.

**Important:** Findings are candidates, not proven leaks. No downstream predictor matrix is certified. This tool never trains, edits source, fetches external data, or authorizes betting. All governance gates remain blocked/unverified.

Next: inspect actual model/evaluation source and predictor selections, add fail-closed column contracts at a *separately reviewed* integration point, and test chronological fold-local fitting. Do not deploy this research helper as a production safety control.
