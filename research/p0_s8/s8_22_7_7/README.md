# S8.22.7.7 — Official NBA November 15 date-level extraction

Offline only. Extracts structured `__NEXT_DATA__` game cards from a hash-verified official NBA date page archived through S8.22.7.2. No new HTTP requests, no automatic provider approval. Optional `--provider-csv` checks matchups only when the CSV exposes explicit team tricodes; tipoff agreement remains **NOT_VERIFIED** until provider timestamp fields and timezone conventions are audited.

The archived NBA page is NOT bundled in the patch. Use your existing local receipt and source files.

```powershell
$Runner = ".\research\p0_s8\s8_22_7_7\run_s8_22_7_7.py"
$Receipt = ".\research\p0_s8\s8_22_7_2\evidence\2023-11-15\21684d55a7e446e4b8da7288d5750d26\receipt.json"
python $Runner --project-root . --date 2023-11-15 --date-receipt $Receipt
```

For optional provider comparison, supply the existing S8.22.7.1 `provider_games.csv` file as `--provider-csv`. If that file uses nested team IDs instead of explicit tricodes, comparison will fail closed; do not alter the source snapshot.

Outputs: `research/p0_s8/s8_22_7_7/results/2023-11-15/official_date_review_<uuid>.json`. The eight official records are retained with official NBA game IDs, teams and UTC tipoffs. All results remain `RESEARCH_ONLY / BLOCK_TRAINING`.
