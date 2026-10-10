# S8.22.10 — Official NBA injury report historical pilot

## Goal

Obtain **one authentic edition** of the official NBA injury-report PDF dated November 15, 2023. Compare its stated edition time against a **60-minute-before-tipoff** cutoff for the eight known games. Do not confuse a date in a filename/PDF with verified publication timing or availability.

Official historical index: https://official.nba.com/nba-injury-report-2023-24-season/

The NBA reports injury statuses such as Out, Doubtful, Questionable, Probable and can list **NOT YET SUBMITTED** teams. These are reports of statuses, not full player eligibility rosters. Any parsing and player-to-game join needs independent manual validation.

## Manual steps

1. Open the official season injury index in a browser. Identify an actual November 15, 2023 report edition and copy the **exact PDF URL** (not just the index URL).
2. Download the PDF once manually. Save it in `research/p0_s8/s8_22_10/manual_input/injury_report.pdf`. If none is available, stop and report the missing evidence.
3. At download time capture UTC time: `(Get-Date).ToUniversalTime().ToString('o') | Set-Content .\research\p0_s8\s8_22_10\manual_input\retrieved_utc.txt`
4. Run:

```powershell
$Pdf = '.\research\p0_s8\s8_22_10\manual_input\injury_report.pdf'
$PdfUrl = Read-Host 'Paste the exact official NBA PDF URL'
$RetrievedUTC = (Get-Content '.\research\p0_s8\s8_22_10\manual_input\retrieved_utc.txt' -Raw).Trim()
python .\research\p0_s8\s8_22_10\run_s8_22_10.py --project-root . --pdf $Pdf --source-url $PdfUrl --retrieved-utc $RetrievedUTC --cutoff-minutes 60
```

The report is saved in a unique append-only evidence folder with source PDF bytes and SHA256. The report must remain `BLOCK_TRAINING` regardless of edition/cutoff comparisons. **The edition label is not a verified historical publication timestamp.**

## Follow-on review gates

- Verify PDF provenance and edition identity against a trustworthy archival source.
- Verify each player row, team and game matchup; handle team `NOT YET SUBMITTED` explicitly.
- Verify true public availability before each prediction cutoff, not merely a printed PDF label.
- Validate that any historical backtest does not access subsequent editions, lineup news or postgame data.
- Review terms/retention before scaling collection. No automatic collection authorized.
