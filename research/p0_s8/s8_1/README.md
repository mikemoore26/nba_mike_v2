# S8.1 — Player game-log quality audit

Run from repository root:

```powershell
python -m pytest -q tests/test_s81_gamelog_quality.py
python research/p0_s8/s8_1/run_s8_1.py --project-root .
```

Reads only `research/p0_s4/s5_1/snapshots/player_gamelogs_{2019-20,2023-24,2025-26}.csv`.
Writes `results/s8_1_report.json`, `results/s8_1_dataset_review.csv`, and `results/s8_1_schema_review.csv`.
No network, model training, odds, or roster-feature promotion. Results are intentionally untracked.
