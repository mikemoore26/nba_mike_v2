# S8.22.10.10 — NBA Public Game Page Evidence

Runs on Python standard library, CPU only. Does not edit previous milestones. Input: one S8.22.10.7 provisional game ID crosswalk. Downloads `https://www.nba.com/game/{away}-vs-{home}-{id}` HTML; preserves raw bytes and SHA-256 receipts under `evidence/2023-11-15/{game_id}/` without overwriting. Writes a derived CSV and review.json to `results/2023-11-15/{crosswalk_sha16}/`.

Commands from project root:

```
python -m pytest tests/test_s8221010_game_pages.py -q
python research/p0_s8/s8_22_10_10/run_s8_22_10_10.py --project-root .
python research/p0_s8/s8_22_10_10/append_docs.py --project-root .
```

`--offline` checks existing snapshots without network; `--timeout 30` adjusts timeout. `--crosswalk`, `--archive`, `--output` override paths. Failed requests are reported per game and do not abort the remaining requests. `TITLE_MATCH_REVIEW_REQUIRED` means only that the HTML page title mentions both teams and the local date. The game ID is supplied in the URL, **not independently verified by this step**. No auto-approval, no training promotion, no historical as-of certification. Never delete raw evidence or bulk-stage results with `git add .`.
