# S8.22.5 — Independent schedule audit

This milestone audits S8.22.4 CSV data offline. It does **not** contact a network, change S8.22.4 or certify a provider. All outputs are research-only.

Run with the most recent S8.22.4 CSV (date must match that file):

```powershell
python .\research\p0_s8\s8_22_5\run_s8_22_5.py --project-root . --date 2026-10-10
```

Outputs under `research/p0_s8/s8_22_5/results/`:
- `s8_22_5_report.json`
- `s8_22_5_comparison.csv`

To validate a known populated date, **manually** invoke the existing S8.22.4 adapter for a date such as 2023-10-24 (historical validation only):

```powershell
python .\research\p0_s8\s8_22_4\run_s8_22_4.py --project-root . --date 2023-10-24 --live
python .\research\p0_s8\s8_22_5\run_s8_22_5.py --project-root . --date 2023-10-24
```

S8.22.4 overwrites its current report/CSV each time; back up prior results first. Live request requires the user's authorization and acceptable provider terms. No automated retries. Do not repeat rapidly on a rate-limited plan.

## Independent comparison (optional)

Acquire a legitimate official schedule file **independently** and record its URL, acquisition date, and licensing/permission. Do not use BALLDONTLIE as its own official reference.

Official schedule CSV columns: `official_nba_game_id,game_date,home_team,away_team,tipoff_utc`. Team map CSV columns: `provider_team_id,official_team`. Team abbreviations must match the official file exactly; mapping must be independently reviewed, not guessed. For example, `DEN` and `LAL` are abbreviation *format* examples, not evidence of a provider ID crosswalk.

```powershell
python .\research\p0_s8\s8_22_5\run_s8_22_5.py --project-root . --date 2023-10-24 --official-csv .\path\official_schedule.csv --team-map-csv .\path\reviewed_team_map.csv --official-source 'NBA official schedule; URL; retrieved YYYY-MM-DD'
```

All matched IDs are **candidate-only**, tipoff tolerance is five minutes, and comparisons remain blocked for training. Empty provider results with a populated independent schedule produce `EMPTY_SCHEDULE_CONTRADICTED_BY_REFERENCE`.

Run tests: `python -m pytest -q tests/test_s8225_schedule_validation.py`.

Governance: `RESEARCH_ONLY / BLOCK_TRAINING`. This milestone does not verify player eligibility, provider entitlement, season completeness, or as-of availability.
