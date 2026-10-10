# S8.22.7.1 — Manual, immutable evidence acquisition

Uses the existing S8.22.4 parser and S8.21 raw-response ledger. Each run creates `captures/YYYY-MM-DD/<unique-id>/provider_games.csv` and `capture_report.json`. Existing captures are never overwritten. No scheduled requests or retries. Live mode requires an API key in the local `.env` and your confirmation that the account terms permit the request. No credentials are written to reports.

Run offline first: `python research/p0_s8/s8_22_7_1/run_s8_22_7_1.py --project-root . --date 2026-10-10 --fixture research/p0_s8/s8_22_4/fixture_games.json`

Run a single permitted live date: `python research/p0_s8/s8_22_7_1/run_s8_22_7_1.py --project-root . --date 2023-11-15 --live --update-manifest`

Manifest update is opt-in. Existing nonempty `provider_csv` values are never overwritten. A valid empty response remains `EMPTY_SCHEDULE_UNVERIFIED`. The independent `reference_csv` is never generated or filled by this tool; acquire separately, preserve its original bytes and retrieval time, and review source provenance. Never commit `.env`, ledger artifacts, captures, or provider results containing licensed data without confirming permissions.
