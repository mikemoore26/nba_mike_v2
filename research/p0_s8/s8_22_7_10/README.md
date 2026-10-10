# S8.22.7.10 — Offline November 15 schedule governance

No network calls, no secret access, no model fitting. Read-only inputs, new report under `results/2023-11-15`.

## Required evidence

- Official NBA date-page receipt and S8.22.7.7 report. Receipt must point to the original `source.bin` under project root.
- Immutable S8.22.7.1 BALLDONTLIE `provider_games.csv` and `capture_report.json`.
- S8.22.7.9 `team_directory_review_*.json`, `verified_team_crosswalk_*.csv`, optionally its receipt (strongly recommended).
- S8.22.7.8 `comparison_*.json`.

Run with explicit `--project-root`, `--official-receipt`, `--official-report`, `--provider-csv`, `--provider-capture-report`, `--directory-review`, `--verified-crosswalk`, `--comparison-report`, and `--directory-receipt` (optional).

The script recomputes archived hashes and reconstructs all 8 games by independently verified team IDs, matchup, and exact tipoff. It does not infer completeness from agreement. The official date-page extraction was retrospective; date completeness stays NOT_CERTIFIED and historical as-of stays NOT_CERTIFIED even if all checks pass. Any issue blocks game agreement. No automated fetching or bypass.

If source artifacts are absent, do not fabricate replacements; restore the original archived evidence or stop.
