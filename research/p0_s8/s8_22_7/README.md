# S8.22.7 — Multi-date reliability (offline)

This is a fail-closed **audit harness**, not a collector or approval. It never calls an API. Edit `date_manifest.csv` to point each date to **distinct preserved provider CSV snapshots** and independently acquired official-reference CSVs. Relative paths are resolved from project root; blank means not yet acquired. The opening-night provider path points to S8.22.4's current results, which may have been overwritten: check `game_date` and SHA256 before running; use a date-specific backup if needed. Do not rerun the S8.22.4 live collector blindly; it overwrites results.

The reference CSV must contain `game_date,official_nba_game_id,home_team,away_team,tipoff_utc,source_url,evidence_sha256,evidence_retrieved_utc`. Only enter real source URLs and SHA256 of acquired raw evidence; never fabricate. A reference CSV with just headers is **not** evidence of a no-game day. A date can only be marked `CANDIDATE_MATCH_REVIEW_REQUIRED`, never approved. Verify the provider terms before any manual live collection.

Run:

```powershell
python -m pytest -q tests/test_s8227_multi_date.py
python research/p0_s8/s8_22_7/run_s8_22_7.py --project-root .
```

Outputs: `results/s8_22_7_report.json`, `results/s8_22_7_date_audit.csv`. No training, no automated schedule approval. Team crosswalk reuses S8.22.6 and is still evidence-review pending. Source fingerprints protect against silent input changes, not source correctness.
