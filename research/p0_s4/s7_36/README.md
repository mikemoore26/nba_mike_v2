# S7.36 — Rejected URL classification

Offline audit of SHA-256-verified S7.34 Bing RSS snapshots. No network access, no transaction or injury evidence promotion.

From repository root:

```powershell
python research/p0_s4/s7_36/run_s7_36.py
Get-Content research/p0_s4/s7_36/results/s7_36_report.json
Import-Csv research/p0_s4/s7_36/results/s7_36_domain_counts.csv | Format-Table -AutoSize
```

Outputs: `results/s7_36_report.json`, `results/s7_36_url_review.csv`, `results/s7_36_domain_counts.csv` (do not commit results). A URL host is only a lead; neither URL structure nor RSS titles verify transaction claims or historical availability. Stop if any source hash fails.
