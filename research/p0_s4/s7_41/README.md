# S7.41 — Offline Article Evidence Recovery

Run from project root with `.venv` active:

```powershell
python -m pytest -q
python .\research\p0_s4\s7_41\run_s7_41.py
Get-Content .\research\p0_s4\s7_41\results\s7_41_report.json
Import-Csv .\research\p0_s4\s7_41\results\s7_41_review.csv | Select-Object player_name,evidence_type,review_status,origin_candidate,destination_candidate,evidence_text | Format-Table -Wrap
```

Requires local S7.38 `results/s7_38_review.csv` and SHA-addressed `results/objects/*.html`. Reads only; does not download or modify upstream evidence. A missing or altered captured article fails closed. Outputs remain untracked research artifacts. **Never promote evidence or train models from this output.**
