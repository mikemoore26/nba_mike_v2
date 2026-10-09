# S8.22.6 — Official schedule cross-validation

Offline only. Source evidence: https://www.nba.com/news/2023-24-nba-regular-season-schedule (opening night matchups, 7:30pm ET and 10pm ET), https://www.nba.com/game/lal-vs-den-0022300061 and https://www.nba.com/game/phx-vs-gsw-0022300062 (NBA game IDs). ET on 2023-10-24 is EDT (UTC-4), so the UTC starts are 2023-10-24 23:30 and 2023-10-25 02:00. This is a curated reference, not a captured raw official schedule artifact.

1. Keep your S8.22.4 historical `s8_22_4_games.csv` for 2023-10-24 in its results folder.
2. Inspect the CSV's `home_provider_team_id` and `away_provider_team_id` values. Enter **actual IDs from your file**, mapping only DEN, LAL, GSW, PHX into `team_crosswalk_review.csv`. Never assume BALLDONTLIE IDs equal official NBA IDs. `evidence_url` and `reviewed_by` should be populated only after independent verification; blank is allowed for research candidates.
3. Run `python -m pytest -q tests/test_s8226_official_validation.py`.
4. Run `python research/p0_s8/s8_22_6/run_s8_22_6.py --project-root . --date 2023-10-24`.
5. Upload `results/s8_22_6_report.json` and `results/s8_22_6_comparison.csv` for review.

If your S8.22.4 results were overwritten, re-run the previously authorized historical-date collection only if your provider terms permit it. Do not share .env or API key.

All mappings are **candidates**. No pregame as-of certification, automated schedule approval, or training.
