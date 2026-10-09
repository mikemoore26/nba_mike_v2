# S8.3 — Historical calendar exception audit

Offline, read-only audit of the three S8.2 game-log snapshots. Identifies the specific 2019–20 game IDs and dates triggering the S8.2 July-1 broad-window warning. The 2020-07-30 through 2020-08-14 interval is a **plausible restart window, not independently verified official schedule evidence**. All rows remain blocked from training.

Run from project root:

```powershell
python .\research\p0_s8\s8_3\run_s8_3.py --project-root .
python -m pytest -q tests/test_s83_calendar.py
```

Outputs under `research/p0_s8/s8_3/results/`: `s8_3_report.json`, `s8_3_game_calendar_review.csv`, `s8_3_dataset_review.csv`. These are generated artifacts; do not Git-stage them. The audit never edits input snapshots and makes no network calls.
