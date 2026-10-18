# S8.22.10.20 — NBA Player Registry Reconciliation

Read-only, offline, fail-closed reconciliation of 44 locally corroborated player names. Never treats a name/team match as certified player identity or historical injury availability.

## First run (inventory; no registry required)

```powershell
python -m pytest .\tests\test_s8221020_player_registry.py -q
python .\research\p0_s8\s8_22_10_20\run_s8_22_10_20.py --project-root .
```

## Optional official NBA registry

Obtain an **unmodified raw JSON response** from the official NBA Stats `CommonAllPlayers` endpoint for the historical 2023-24 season, save it outside tracked source directories (e.g. `research/p0_s8/s8_22_10_20/evidence/commonallplayers_2023_24.json`), and record the exact request URL, retrieval time, season parameters, and source URL separately. The script does **not** fetch it and cannot authenticate its provenance from its contents alone. Do not substitute third-party IDs or a hand-built player list.

```powershell
python .\research\p0_s8\s8_22_10_20\run_s8_22_10_20.py --project-root . --registry-json .\research\p0_s8\s8_22_10_20\evidence\commonallplayers_2023_24.json
```

Output: `results/2023-11-15/<hash>/player_registry_candidates.csv` and `review.json`. Results are hash-scoped; source ledgers and prior results are not modified. Team mismatch, missing team, duplicate IDs, and unknown names do not receive proposed IDs. Registry matches remain **candidates** because historical season, registry provenance, roster changes, injury status and as-of publication time require separate verification.

After a successful run:

```powershell
python .\research\p0_s8\s8_22_10_20\append_docs.py --project-root .
```

Governance: `RESEARCH_ONLY / BLOCK_TRAINING`.
