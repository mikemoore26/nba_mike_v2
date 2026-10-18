# S8.22.10.22A — installed nba_api player registry

Run from the repository root with the existing virtual environment active:

```powershell
python -m pytest .\tests\test_s8221022a_local_registry.py -q
python .\research\p0_s8\s8_22_10_22a\run_s8_22_10_22a.py --project-root .
python .\research\p0_s8\s8_22_10_22a\append_docs.py --project-root .
```

This **does not use the internet**. It imports `nba_api.stats.static.players.get_players()` from the installed package, captures a normalized name/ID snapshot, and records the package version, absolute module location, module SHA-256, snapshot SHA-256 and capture time. Output: `results/2023-11-15/<hash>/installed_nba_api_players.json`, `third_party_name_only_adapter.json`, `player_id_candidates.csv`, and `capture_manifest.json`.

The reconciliation requires the original hash-matched S8.22.10.7 ledger, S8.22.10.18 diagnostic, and corroborated S8.22.10.19 evidence. Every player is marked as unique name candidate, ambiguous, or unmatched. **No identity is certified**. A local package directory does not verify the historical 2023-11-15 roster, injury status, or as-of publication. The adapter contains blank team fields and is *not* an official NBA Stats response. Keep `RESEARCH_ONLY / BLOCK_TRAINING`.

S8.22.10.21 and S8.22.10.22 may remain as earlier uncommitted acquisition attempts; this patch adds new files rather than overwriting them. Generated results are not staged automatically. Do not use `git add .`.
