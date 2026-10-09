# S8.13 — Training Boundary Architecture (research only)

This package is a deliberately non-executable training boundary. `require_training_authorization` always raises `BoundaryDenied`; there is no model fit/predict dispatcher. A self-reported `VERIFIED` evidence record is marked `CLAIMED_UNVALIDATED`, never accepted as independent proof.

From repository root:

```powershell
python -m pytest -q tests/test_s813_boundary.py
python .\research\p0_s8\s8_13\run_s8_13.py --project-root .
```

Outputs: `results/s8_13_report.json`, `results/s8_13_cases.csv` (local, generated). Requires installed pandas/numpy and S8.10 `contract.py`. Does not access network, modify source features, fit estimators, or authorize training.

**Next step:** independently establish historical as-of publication evidence and pregame player eligibility; then design a separately reviewed training-service implementation. Do not replace the unconditional denial based only on user-supplied evidence metadata.
