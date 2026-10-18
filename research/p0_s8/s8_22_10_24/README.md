# S8.22.10.24 — Historical game-day boxscore acquisition

Run on Windows from the project root with `.venv` active:

```powershell
python -m pytest .\tests\test_s8221024_espn_capture.py -q
python .\research\p0_s8\s8_22_10_24\run_s8_22_10_24.py --project-root .
python .\research\p0_s8\s8_22_10_24\append_docs.py --project-root .
```

Uses the public ESPN NBA scoreboard for **2023-11-15** and ESPN event summaries. It retrieves real third-party source responses, stores raw bytes, URLs, capture timestamps and SHA-256 hashes, and links game-day boxscore *listings* to the 44 `nba_api` name-only candidates. A listing is **not** roster contract proof; a missing listing is **not** evidence that the player was off the team. Names alone can misidentify people, and ESPN athlete IDs are not NBA person IDs. DNP and injured athletes may appear in boxscore listings; participation is not asserted.

Requires network access to `site.api.espn.com`; if unavailable or data structure differs, the run fails closed. Does not accept synthetic fixture data in production. Raw captures under `results/` should be preserved as research artifacts; don't stage them indiscriminately. Review manifest and CSV before committing.

Governance remains `RESEARCH_ONLY / BLOCK_TRAINING`. This milestone does not certify player IDs, date-specific roster membership, injuries, or report publication time.
