# S8.22.7.3 — Multi-source official NBA game references

**Offline, fail-closed.** Read already archived official NBA `receipt.json` and `source.bin` files. For each receipt, verify the source SHA-256, size, date, official NBA URL and structured JSON-LD SportsEvent (game ID from canonical NBA URL, home/away abbreviations and tipoff converted to UTC). A row in the resulting CSV points to its *own* original source URL, SHA-256 and receipt timestamp.

## Commands (Windows PowerShell, from project root)

```powershell
$Runner = '.\research\p0_s8\s8_22_7_3\run_s8_22_7_3.py'
python $Runner --project-root . --date 2023-10-24 `
  --receipt '.\research\p0_s8\s8_22_7_2\evidence\2023-10-24\e870d83d313c4c389bffdf8ea4d09e59\receipt.json' `
  --receipt '.\research\p0_s8\s8_22_7_2\evidence\2023-10-24\0d055e3672294eafb11afe27a27c9b47\receipt.json' `
  --provider-csv '.\research\p0_s8\s8_22_4\results\s8_22_4_games.csv' `
  --crosswalk '.\research\p0_s8\s8_22_6\team_crosswalk_review.csv'
```

Check that your provider CSV is still the Oct 24 snapshot; if it was overwritten, locate the date-specific S8.22.7.1 capture and use that CSV instead. The `--provider-csv` and `--crosswalk` arguments are optional together; omitting them still builds the official reference CSV.

Output: `research/p0_s8/s8_22_7_3/results/2023-10-24/official_reference_<id>.csv` and `report_<id>.json`. When provider snapshot supplied, a provisional comparison is printed, *not* date completeness certification. Source snapshots are never modified.

**Critical**: S8.22.7.3 does not modify the S8.22.7 manifest because game-page evidence alone cannot prove the full day's schedule. To include the reference in the main multi-date audit, first obtain independent date-level completeness evidence and document a human review; then manually set the manifest `reference_csv` field to the new CSV path. Never assume that 2 matching games prove there were only 2 games. Never treat contemporary pages as proof of historical pregame availability.

No network calls, API keys, model training, betting, or routine collection. Governance: RESEARCH_ONLY / BLOCK_TRAINING.
