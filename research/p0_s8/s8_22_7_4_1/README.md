# S8.22.7.4.1 — Official announcement validation correction

S8.22.7.4 incorrectly required official NBA game IDs to occur in an announcement page, although that page identifies games by team names and tipoff times. This **separate runner** does not overwrite the original validator.

It verifies the S8.22.7.2 archived page bytes against its receipt, extracts visible HTML text, and checks that reviewed matchup, tipoff, and date-coverage quotes appear in that page. It compares those reviewed rows with S8.22.7.3's independently sourced per-game IDs, teams, and UTC tipoffs. The announcement itself need not include game IDs.

`reviewed_2023-10-24_CANDIDATE.csv` is a **draft** based on the archived official NBA schedule announcement. Inspect the archived page and verify each row before use. Quote presence does not prove that each quote semantically supports a game or that the announcement is an exhaustive schedule. A human must interpret its doubleheader statement.

## Run in PowerShell

```powershell
$Runner = ".\research\p0_s8\s8_22_7_4_1\run_s8_22_7_4_1.py"
$Receipt = ".\research\p0_s8\s8_22_7_2\evidence\2023-10-24\c2f5a8440d1f43c2b65ce0077c4dc524\receipt.json"
$Reference = Get-ChildItem ".\research\p0_s8\s8_22_7_3\results\2023-10-24" -Filter "official_reference_*.csv" |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
python $Runner --project-root . --date 2023-10-24 `
  --date-receipt $Receipt `
  --reviewed-date-csv ".\research\p0_s8\s8_22_7_4_1\reviewed_2023-10-24_CANDIDATE.csv" `
  --game-reference-csv $Reference.FullName
```

The archived announcement is **not** bundled; reuse locally saved receipt and source. Reports go under `research/p0_s8/s8_22_7_4_1/results/2023-10-24/`.

No network access, no `.env` use, no manifest updates, no date-completeness or historical-as-of certification. RESEARCH_ONLY / BLOCK_TRAINING.
