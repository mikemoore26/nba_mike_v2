# S8.22.10.17 — Player identity and injury evidence inventory

Offline, fail-closed inspection of the **44 player candidates** in the 54-row November 15, 2023 ledger. The other 10 team-submission notices are not individual injury statuses and are excluded. Uses exact SHA-256 checks for original ledger and S8.22.10.14 triage. No remote requests, no edits to upstream files, no invented NBA player IDs or historical publication times.

## Run from repository root

```powershell
python -m pytest .\tests\test_s8221017_player_evidence.py -q
python .\research\p0_s8\s8_22_10_17\run_s8_22_10_17.py --project-root .
python .\research\p0_s8\s8_22_10_17\append_docs.py --project-root .
```

Outputs in `research/p0_s8/s8_22_10_17/results/2023-11-15/<hash>/`:
- `review.json`: counts and source fingerprints
- `player_identity_evidence_audit.csv`: all 44 candidate diagnostics
- `review_priority_queue.csv`: candidates with additional name, excerpt, mapping, or duplicate issues

`PLAUSIBLE_FORMAT_ONLY` and `CANDIDATE_NAME_PRESENT` do **not** certify identity or original PDF accuracy. There is no authoritative NBA player-ID source or timestamped injury source integrated at this step. All rows remain **NOT_CERTIFIED**, `training_eligible=NO`, `RESEARCH_ONLY / BLOCK_TRAINING`.

If a SHA-256 check fails, stop and investigate rather than changing expected hashes to match unknown data. Source evidence artifacts stay untracked unless explicitly reviewed for safe inclusion.
