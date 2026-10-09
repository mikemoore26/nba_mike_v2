# S8.6 — Read-only feature code leakage triage

Run from project root:

```powershell
python -m pytest -q
python .\research\p0_s8\s8_6\run_s8_6.py --project-root .
```

Outputs are in `research/p0_s8/s8_6/results/`: `s8_6_report.json`, `s8_6_findings.csv`, `s8_6_file_inventory.csv`.

This is an intentionally conservative, heuristic scanner. It does not certify the code or establish true pregame provenance. Review candidate findings manually and preserve source hashes. No training, model execution, or changes to S5/S6 code.
