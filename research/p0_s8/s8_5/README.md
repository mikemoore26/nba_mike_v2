# S8.5 — Historical feature-lineage feasibility

Offline, read-only audit of S5.1 player game-log snapshots. No network, no changes to inputs, no model training.

Run from project root:

```powershell
python -m pytest tests/test_s85_lineage.py -q
python .\research\p0_s8\s8_5\run_s8_5.py --project-root .
```

Outputs (untracked): `results/s8_5_report.json` and `results/s8_5_dataset_review.csv`.

Strictly earlier **calendar dates** only are used to demonstrate player-history feasibility. Same-day records are not considered prior history; same-game outcomes never enter the same-game feature set. Demonstration eligibility is not training eligibility. Player participation itself is a postgame selection issue; historical pregame player universe and publication/as-of proof remain unverified.

S8.4's 88 official schedule matches are still unavailable after NBA Stats timeout. Do not repeat identical endpoint attempts. Reopen only with a demonstrably accessible independent official source. Do not promote S7 roster/injury or market fields.
