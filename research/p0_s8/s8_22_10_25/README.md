# S8.22.10.25 — Adjacent-game ESPN evidence

**Research-only; training blocked.** Retrieves ESPN scoreboard and game summaries for November 14, 16, 17 and 18, 2023, seeking leads for 35 injury-report players absent from the November 15 boxscore. It does **not** assert membership on the target date.

Run from repository root:

```powershell
python -m pytest .\tests\test_s8221025_adjacent_evidence.py -q
python .\research\p0_s8\s8_22_10_25\run_s8_22_10_25.py --project-root .
python .\research\p0_s8\s8_22_10_25\append_docs.py --project-root .
```

You may specify `--dates 2023-11-14 2023-11-16` for a shorter diagnostic, but the report directory requires a single completed capture; do not mix date-window captures when updating docs. A successful run writes immutable raw JSON responses, a listing extract, a 44-player CSV, and a review manifest with source URLs, capture timestamps, and hashes. A failed run must not be interpreted as evidence of player absence. **Do not commit raw source evidence without reviewing licensing and repository policy.**

The previous S8.22.10.24 unpacking fix `mf,path,m=matches[0]` must be preserved and committed with this milestone if not already committed.
