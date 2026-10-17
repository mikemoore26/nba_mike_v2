# S8.22.10.11 — independent NBA schedule-link discovery

Run `python -m pytest tests/test_s8221011_schedule.py -q`, then `python research/p0_s8/s8_22_10_11/run_s8_22_10_11.py --project-root .`. This attempts to retrieve `https://www.nba.com/games?date=2023-11-15`, archives immutable HTML and SHA-256 receipt, and extracts game IDs **only from actual HTML anchor hrefs** (never from existing crosswalk or scripted embedded IDs). Compare discovered IDs with S8.22.10.7 and S8.22.10.10 archived title evidence. The NBA site may render schedules client-side, in which case zero links may be extracted; this is a valid fail-closed result. A blocked response is also fail-closed.

For an independently obtained HTML file, optionally use `--schedule-html path/to/file.html` to archive it once. This does NOT establish that the file was actually from the NBA: reviewer must check provenance. `--offline` reuses an existing archive without HTTP requests. Never overwrite archived HTML or receipts. Outputs: `research/p0_s8/s8_22_10_11/results/2023-11-15/<crosswalk-hash>/review.json` and `independent_schedule_reconciliation.csv`.

Review results before running `python research/p0_s8/s8_22_10_11/append_docs.py --project-root .`. No game IDs or injury rows are automatically certified; historical as-of and training remain blocked.
