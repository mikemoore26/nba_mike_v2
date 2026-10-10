# S8.22.9 — Historical pregame source discovery

Offline research shortlist. No network requests, authentication, model fitting, or collection permission.

Run from repository root:

```powershell
python -m pytest .\tests\test_s8229_sources.py -q
python .\research\p0_s8\s8_22_9\run_s8_22_9.py --project-root .
python .\research\p0_s8\s8_22_9\append_docs.py --project-root .
```

Source facts and qualifications: `source_candidates.json`. Every historical 2023 as-of claim remains unverified. Candidate ranking is research priority, not provider endorsement. Reports generated in `results/` are local artifacts and are not staged automatically.
