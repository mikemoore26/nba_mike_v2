# S8.22 — NBA schedule collector (manual, research only)

Requires S8.21 at `research/p0_s8/s8_21/run_s8_21.py`.

Offline test: `python -m pytest -q tests/test_s822_schedule.py`

Offline run:
`python research/p0_s8/s8_22/run_s8_22.py --project-root . --fixture research/p0_s8/s8_22/fixture_schedule.json`

Live, opt-in one request (verify permission and endpoint accessibility first):
`python research/p0_s8/s8_22/run_s8_22.py --project-root . --live`

Source candidate: `https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json`.
This URL and schema are provisional; current live accessibility was not verified during packaging. HTTP failures are recorded in S8.21; the CLI exits with status 2 on failed parsing or retrieval. No background scheduling, scraping bypass, betting, or model fitting.

Outputs:
- `research/p0_s8/s8_22/results/s8_22_report.json` latest receipt
- `research/p0_s8/s8_22/results/s8_22_games.csv` latest normalized games (empty on errors)
- `research/p0_s8/s8_22/results/s8_22_receipt_<event_id>.json` per-attempt metadata (append-only filename)
- S8.21 `artifacts/capture_ledger.sqlite3` and `blobs/` preserve retrieval bytes or failures.

Do not commit generated results, S8.21 ledger or blobs. Raw schedule bytes are retained even if parser validation fails. This collector uses `SCHEDULE_FEED` as a ledger feed ID, **not a real NBA game ID**. Checkpoints are user-provided labels, not proof that a request happened that far before any game. Receipt time from S8.21 is authoritative for local receipt, not independent historical publication certification. Publisher dates and response headers do not certify as-of availability. All outputs remain RESEARCH_ONLY / BLOCK_TRAINING.
