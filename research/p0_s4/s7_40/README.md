# S7.40 — Transaction Evidence Quality & Direction Review

Offline analysis of S7.39's emitted CSV. Does not download articles or promote evidence.

From the NBA_MIKE v2 project root:

```powershell
python -m pytest -q
python .\research\p0_s4\s7_40\run_s7_40.py
Get-Content .\research\p0_s4\s7_40\results\s7_40_report.json
Import-Csv .\research\p0_s4\s7_40\results\s7_40_review.csv | Select-Object player_name,review_status,origin_candidate,destination_candidate,quality_flags,statement | Format-Table -Wrap
```

Outputs: `results/s7_40_review.csv` and `results/s7_40_report.json`. Do not commit generated results or captured article objects. Labels are **review-only**; neither player/team histories nor historical publication are verified. S7.39's report double-counted no-match rows, so this stage calculates totals from its actual CSV records. Does not edit S7.39 files.
