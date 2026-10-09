# S7.43 — Event identity and source independence (offline)

Run from repository root:

```powershell
python research/p0_s4/s7_43/run_s7_43.py
```

Inputs: S7.42 review CSV and S7.38 SHA-addressed HTML objects. Outputs: `results/s7_43_report.json`, `results/s7_43_review.csv`. Does not download anything. Never equates tracker event date with article event date; never treats URL/domain variety as editorial independence. `RESEARCH_ONLY / BLOCK_TRAINING`.
