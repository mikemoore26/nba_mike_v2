# P0-S3 S2 — Storage & Manifest Standard

This milestone turns the S1 storage architecture into an enforceable provenance layer.

Run from project root:

```powershell
python -m pytest .\tests\test_storage_manifest.py -q
python .\research\p0_s3\s2\run_s2_acceptance.py
```

Acceptance requires directory creation, artifact registration, SHA-256 verification, manifest round-trip, tamper detection, quarantine behavior, and cache separation to pass.

This milestone does not download NBA data and does not authorize model training.
