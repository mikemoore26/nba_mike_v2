# S8.22.7.9 — Independent BALLDONTLIE team directory verification

Offline-only verification of S8.22.7.8's 16 candidate team IDs against archived bytes from the provider's `/v1/teams` directory. The game records are **not** accepted as team-identity evidence.

## Required evidence

1. Review BALLDONTLIE API terms and your permitted account access.
2. Manually retrieve the full `https://api.balldontlie.io/v1/teams` JSON using your own authenticated client, **without sharing your API key**. Do not embed the key in the URL, filenames, source JSON, or receipt. No automated fetching is included here.
3. Save the unmodified JSON response locally as `source.bin` in a unique evidence folder. Use the supplied offline `make_team_receipt.py` to generate a SHA-256 receipt. This is a new research snapshot, not historical pregame evidence.
4. Run the offline validator against your existing S8.22.7.8 candidate crosswalk and `comparison_*.json`.

Example PowerShell from project root:

```powershell
$EvidenceDir = ".\research\p0_s8\s8_22_7_9\evidence\manual_team_directory_$(Get-Date -Format yyyyMMddHHmmss)"
New-Item -ItemType Directory -Force $EvidenceDir | Out-Null
# Manually save the *unmodified*, authorized /v1/teams JSON response to "$EvidenceDir\source.bin".
python .\research\p0_s8\s8_22_7_9\make_team_receipt.py --project-root . --source "$EvidenceDir\source.bin" --retrieved-utc "2026-10-10T01:00:00Z"
# Replace retrieved-utc with the REAL UTC time of your capture; never fabricate it.
$Receipt = Join-Path $EvidenceDir 'receipt.json'
$Comparison = Get-ChildItem .\research\p0_s8\s8_22_7_8\results -Filter 'comparison_*.json' -Recurse | Sort-Object LastWriteTime -Descending | Select-Object -First 1
python .\research\p0_s8\s8_22_7_9\run_s8_22_7_9.py --project-root . --team-receipt $Receipt --crosswalk-csv .\research\p0_s8\s8_22_7_8\team_crosswalk_CANDIDATE.csv --comparison-report $Comparison.FullName
```

**Do not run the example until the actual team JSON has been captured.** If you already have an archived team-directory response, reuse it after validating provenance; do not repeat a live call. Never upload `.env` or authorization headers.

Reports are under `research/p0_s8/s8_22_7_9/results/2023-11-15`. Team identity can be independently supported by directory bytes while historical as-of, date completeness, and model training remain blocked.
