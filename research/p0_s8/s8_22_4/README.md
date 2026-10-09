# S8.22.4 — BALLDONTLIE schedule adapter

Manual, one-request NBA Games retrieval. No retries, scheduler, model fitting or betting. Requires existing S8.21 capture infrastructure and `python-dotenv`.

## Commands (PowerShell, project root)

```powershell
python -m pip install python-dotenv
python -m pytest -q tests/test_s8224_balldontlie.py
python research/p0_s8/s8_22_4/run_s8_22_4.py --project-root . --date 2026-10-10 --fixture research/p0_s8/s8_22_4/fixture_games.json
python research/p0_s8/s8_22_4/run_s8_22_4.py --project-root . --date 2026-10-10 --live
```

`--live` is **explicit opt-in**; only run after reviewing your BALLDONTLIE plan and terms. Key is read from project-root `.env` (`BALLDONTLIE_API_KEY=...`) or environment, never written into results. Do not share the `.env` file. Confirm `git check-ignore -v .env`.

Outputs: `research/p0_s8/s8_22_4/results/s8_22_4_report.json` and `s8_22_4_games.csv`. Raw bytes and event are written to `research/p0_s8/s8_21/artifacts/`. The S8.21 event timestamp is the capture receipt time. Provider game IDs are not NBA official IDs. `tipoff_status=PRESENT_UNVERIFIED` is not proof of tipoff accuracy.

A nonzero exit on an API or parsing failure is intentional. Do not repeatedly retry HTTP 403/429. If response has `next_cursor`, the adapter rejects incomplete pagination instead of presenting partial game coverage. Report and CSV are overwritten per run; raw S8.21 capture events remain append-only. Upload report/CSV after the live run, not raw blobs or credentials.
