# S8.22.10.15 — Game-mapping exception diagnosis

Run after S8.22.10.14 has produced its 54-row report and four exceptions.

```powershell
python -m pytest .\tests\test_s8221015_mapping_exceptions.py -q
python .\research\p0_s8\s8_22_10_15\run_s8_22_10_15.py --project-root .
python .\research\p0_s8\s8_22_10_15\append_docs.py --project-root .
```

Offline, read-only input. Fails closed if the upstream report, record count, exception count, or exception reasons differ. Produces `mapping_exception_analysis.csv` and `review.json` in a hash-named `results/2023-11-15/` directory. Team-to-game suggestions are permitted only for same-date, unique-team cases without conflicting matchup evidence. They are **not** changes to the original ledger, injury certification, or permission to train. Examine results before planning the next milestone.
