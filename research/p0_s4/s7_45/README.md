# S7.45 — Publication metadata reconciliation

Offline only. Requires `research/p0_s4/s7_44/results/s7_44_review.csv` from S7.44.

Run from project root:

```powershell
python .\research\p0_s4\s7_45\run_s7_45.py
Get-Content .\research\p0_s4\s7_45\results\s7_45_report.json
Import-Csv .\research\p0_s4\s7_45\results\s7_45_review.csv | Select-Object player_names,publication_dates,modified_dates,publication_conflict,archive_priority | Format-Table -AutoSize
```

No network, no article fetching, no historical proof. Generated results are local and not included in the patch.
