# S8.22.10.22 — fallback NBA player identity registry

Run from project root after extracting patch:

```powershell
python -m pytest .\tests\test_s8221022_fallback_registry.py -q
python .\research\p0_s8\s8_22_10_22\run_s8_22_10_22.py --project-root . --reconcile
python .\research\p0_s8\s8_22_10_22\append_docs.py --project-root .
```

Default acquisition downloads the `nba_api` community project's static player list from GitHub Raw. It is **third-party, mutable `master`**, not an official historical 2023–24 NBA roster. `--offline-json <file>` accepts a separately obtained copy in the exact `nba_api` static player list schema (`[{"id": 123, "full_name": "..."}]`); such a copy is marked **USER_SUPPLIED_UNVERIFIED_SOURCE**, even if its content matches expected schema. No generated fixture is evidence. `--timeout 15` can be adjusted up to 60 seconds. Acquisition failure returns code 2 and leaves documentation untouched.

A validated raw capture, manifest and **name-only adapter** are stored in `results/2023-11-15/<sha-prefix>/`. The adapter uses the field names understood by S8.22.10.20 but is **not** NBA Stats data; `TEAM_ABBREVIATION` is deliberately empty because this source does not establish team on 2023-11-15. Matching names may yield player-ID *candidates*, not certified IDs. No injury status, historical team or historical publication time is certified. Research stays `RESEARCH_ONLY / BLOCK_TRAINING`.

Never stage the results directory automatically; review evidence provenance and privacy before selecting what to commit. Do not run `git add .`.
