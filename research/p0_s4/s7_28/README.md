# S7.28 — Official trade tracker candidate parser

Run from project root after S7.27:

```powershell
python .\research\p0_s4\s7_28\run_s7_28.py
```

Requires the original S7.27 HTML object and candidate CSV. SHA-256 must match. Outputs `results/s7_28_review.csv` and `results/s7_28_report.json`. Optionally pass `--id-map PATH` with columns `player_id,player_name,source_url` from independently obtained stable-ID evidence. **No automatic S7.26 import or historical as-of training eligibility.**
