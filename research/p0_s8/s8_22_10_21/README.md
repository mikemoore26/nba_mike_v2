# S8.22.10.21 — NBA registry acquisition

Runs a bounded HTTPS request to the NBA Stats `CommonAllPlayers` endpoint for `Season=2023-24` and `LeagueID=00`, preserves the raw response and capture manifest, and validates the response with the S8.22.10.20 parser. The request can be blocked by NBA CDN restrictions; a failure does not create a fabricated registry. Run from the repository root:

```powershell
python -m pytest .\tests\test_s8221021_registry_acquisition.py -q
python .\research\p0_s8\s8_22_10_21\run_s8_22_10_21.py --project-root . --reconcile
```

If NBA access fails, retain the error output and do **not** run the docs updater. An existing **authentic unmodified** NBA Stats response may be processed offline:

```powershell
python .\research\p0_s8\s8_22_10_21\run_s8_22_10_21.py --project-root . --offline-fixture "C:\path\to\official_response.json" --reconcile
```

Offline files are explicitly labeled `OFFLINE_FIXTURE_UNVERIFIED` and their origin is not authenticated by this command. Do not substitute invented sample data for a real source. After successful capture and reconciliation, run `append_docs.py --project-root .`.

**Limits:** the endpoint's season parameter and TEAM_ABBREVIATION are not proof of team affiliation on 2023-11-15. Current retrieval timestamps are not historical injury-report publication timestamps. Player identities, injury statuses and historical as-of remain uncertified; `RESEARCH_ONLY / BLOCK_TRAINING`.
