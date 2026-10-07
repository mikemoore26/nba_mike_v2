# P0-S3 S7 — Leakage & Invariant Test Suite

Purpose: turn the canonical data contracts into executable fail-closed checks before historical reconstruction or model training.

The suite deliberately injects invalid states and requires rejection of target-day/future statistical data, duplicate player-game keys, team=opponent rows, target/outcome fields inside feature rows, malformed D-1 metadata/provenance, false zero-history status, and non-PASS snapshot parents.

Run:

```powershell
python -m pytest .\tests\test_leakage_invariants.py -q
python -m pytest -q
python .\research\p0_s3\s7\run_s7_acceptance.py
```

Pass requires all targeted tests, the full regression suite, and the S7 acceptance runner to pass. This milestone does not authorize model training.
