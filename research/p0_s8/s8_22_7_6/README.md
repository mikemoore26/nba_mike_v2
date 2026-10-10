# S8.22.7.6 — Independent schedule evidence acquisition queue

This milestone **does not fetch anything**. It consumes the actual S8.22.7.5 JSON report and generates a five-date, prioritized acquisition queue. No certification or training.

## Workflow

1. Run S8.22.7.5, and identify its `coverage_*.json` report.
2. Run this script with `--coverage-report` relative to project root.
3. Read the generated `acquisition_queue_*.csv` and collect only evidence that is needed.
4. If you manually capture official NBA date-level evidence using existing S8.22.7.2 procedures (after reviewing applicable terms), save the `receipt.json` and `source.bin` together. Fill the *optional* `receipt_manifest_TEMPLATE.csv` with project-relative `receipt.json` paths and rerun with `--receipt-manifest`.
5. `PASS_BYTES_ONLY` validates source SHA-256, byte size, URL host, receipt date, and retrieval timestamp; **not** date completeness, source semantics, or historical pregame availability. Manual review is still required.

### PowerShell

```powershell
$Coverage = Get-ChildItem '.\research\p0_s8\s8_22_7_5\results' -Filter 'coverage_*.json' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $Coverage) { throw 'Run S8.22.7.5 first' }
$Relative = [IO.Path]::GetRelativePath((Get-Location).Path, $Coverage.FullName)
python .\research\p0_s8\s8_22_7_6\run_s8_22_7_6.py --project-root . --coverage-report $Relative
```

Optional after capturing sources:

```powershell
python .\research\p0_s8\s8_22_7_6\run_s8_22_7_6.py --project-root . --coverage-report $Relative --receipt-manifest 'research/p0_s8/s8_22_7_6/receipt_manifest_TEMPLATE.csv'
```

## Priorities

- CONTROL: 2023-10-24 — preserve candidate agreement, do not duplicate captures.
- P1: 2023-11-15 — eight provider games, official full-date reference absent.
- P2: 2024-01-15 — eleven provider games, official full-date reference absent.
- P3: 2024-06-20 — zero rows; requires independent **negative** schedule evidence.
- P4: 2026-10-10 — zero rows; separately establish **preseason** source scope.

The queue never changes S8.22.7.5 manifests or stored evidence. It performs no requests, credential use, schedule certification, training or provider approval. All outputs remain `BLOCK_TRAINING`.
