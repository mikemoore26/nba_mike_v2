# S8.22.10.13 — Automated Game-ID Evidence Verification

This milestone **does not** invent a human reviewer or approve a manual worksheet. It calls the S8.22.10.12 offline auditor and automatically labels the eight Nov 15, 2023 games `AUTOMATED_VERIFIED` **only** when archived schedule and page receipts, bytes, SHA-256, dates, matchup, page-title status, and discovered game IDs all agree. Otherwise it emits `MANUAL_EXCEPTION_REQUIRED`. No training gate changes.

## Run (Windows PowerShell from project root)

```powershell
python -m pytest .\tests\test_s8221012_certification.py .\tests\test_s8221013_automation.py -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
python .\research\p0_s8\s8_22_10_13\run_s8_22_10_13.py --project-root .
if ($LASTEXITCODE -ne 0) { throw 'Automated verification failed' }
python .\research\p0_s8\s8_22_10_13\append_docs.py --project-root .
```

Outputs are under `research/p0_s8/s8_22_10_13/results/2023-11-15/<evidence-token>/`: `review.json`, `automated_game_id_verification.csv`, `manual_exception_queue.csv`. Evidence inputs and S8.22.10.12 manual worksheet are never edited. The crosswalk is found in the actual S8.22.10.7 results and must match full expected SHA-256 `ca59d35f24e2ac8c1ba70971b5fec60ec7ce654a938b4d9d1902848f8d115212`; zero or multiple matching candidates fail closed. `--crosswalk` can override the location but **not** the hash. `--schedule-reconciliation` and `--page-evidence` support explicit input paths.

**Interpretation:** automated local integrity/identity agreement is *not* independently authenticated publisher provenance, historical as-of availability, human review, player identity certification, or permission to train. `RESEARCH_ONLY / BLOCK_TRAINING` is unchanged. Next: triage 54 injury-report records with separate identity and as-of safeguards.
