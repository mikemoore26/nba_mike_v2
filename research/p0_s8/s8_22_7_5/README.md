# S8.22.7.5 — Offline historical schedule coverage expansion

**Research only; always BLOCK_TRAINING.** No API calls, automated downloads, training, or manifest modification. This stage compares **five dates**, with separate handling for zero-provider-result dates.

## Prepare

1. Open `coverage_manifest.csv` and fill `provider_csv` from the existing S8.22.7 `date_manifest.csv` for all five dates (the file paths must exist). Do not modify the S8.22.7 manifest.
2. For 2023-10-24, set `official_reference_csv` to the S8.22.7.3 two-game reference and `announcement_report_json` to the S8.22.7.4.1 report. These are candidate inputs, not date-completeness certification.
3. For 2023-11-15 and 2024-01-15, leave `official_reference_csv` blank until independent, row-provenanced NBA references exist. If independently archived date-level evidence and manually reviewed game list exist, fill `date_receipt_json` and `reviewed_date_csv`. These are **separate** from provider snapshots and must not be copied from provider output.
4. For zero-result dates, optionally set `negative_evidence_receipt_json` to an archived official NBA date-level source. Even with that receipt, this tool will **not** certify a no-game date: a human must inspect source coverage and semantics. The 2026-10-10 preseason case is especially sensitive to schedule/provider scope.
5. Every path in the manifest is relative to the project root. Never paste credentials, `.env`, or API keys.

## Run (PowerShell)

```powershell
python .\research\p0_s8\s8_22_7_5\run_s8_22_7_5.py --project-root .
python -m pytest -q tests/test_s82275_coverage.py
Get-ChildItem .\research\p0_s8\s8_22_7_5\results\coverage_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

`results/coverage_<uuid>.json` and `.csv` are generated and intentionally not included in the patch. Upload the JSON for review. **No model training or routine collection approval.**

## Important limits

- An official game-page reference CSV alone cannot prove full date coverage. An announcement candidate report also requires human review.
- This runner checks CSV metadata/provenance format but does not rehash every game-page `source.bin`; rely on S8.22.7.3 provenance review and rerun that verifier when needed.
- Zero-row provider snapshots never produce `NO_GAMES_CERTIFIED`.
- No source is fabricated for dates without evidence.
