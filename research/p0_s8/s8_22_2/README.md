# S8.22.2 Alternative schedule source evaluation

Offline and read-only source comparison. Python standard library only. Run:

```powershell
python -m pytest -q tests/test_s8222_sources.py
python research/p0_s8/s8_22_2/run_s8_22_2.py --project-root .
```

Outputs in `research/p0_s8/s8_22_2/results/`: JSON report, CSV source matrix, CSV acceptance gates. No network, ingestion, model fitting, or live source authorization. Do not treat undocumented ESPN endpoints as licensed APIs. A provider must pass all acceptance gates before a manual live adapter is built. Generated outputs should not be committed.
