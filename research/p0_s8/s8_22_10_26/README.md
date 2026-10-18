# S8.22.10.26 — Opening-week readiness audit

Run from the project root:

```powershell
python -m pytest .\tests\test_s8221026_readiness.py -q
python .\research\p0_s8\s8_22_10_26\run_readiness_audit.py --project-root .
python .\research\p0_s8\s8_22_10_26\append_docs.py --project-root .
```

The script inventories relevant code/docs using filenames and text signals, saves JSON and CSV to `results/`, and **does not execute model code, scrape live markets, train models, or approve bets**. File presence is not evidence of a working model. The next step is to review actual repository candidates and test operational gates. Results should not be committed by default.
