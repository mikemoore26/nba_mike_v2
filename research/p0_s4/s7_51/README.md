# S7.51 — Evidence Bottleneck Decision Gate

Offline analysis of `../s7_50/results/s7_50_review.csv`. Does not download data, edit prior results, or enable training.

Run from project root:

```powershell
python -m pytest -q
python .\research\p0_s4\s7_51\run_s7_51.py
Get-Content .\research\p0_s4\s7_51\results\s7_51_report.json
Import-Csv .\research\p0_s4\s7_51\results\s7_51_review.csv | Format-Table -AutoSize
```

Outputs: `s7_51_report.json`, `s7_51_review.csv`, `s7_51_article_inventory.csv`. Results remain local/untracked. Do not interpret the number of review rows as independent articles. Classification prioritizes missing player/team mapping, then capture availability, then direction strength. It is an operational decision aid, not historical proof.
