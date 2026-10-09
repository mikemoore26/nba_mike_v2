# S8.21 — Offline forward evidence capture prototype

No external requests, real-world pregame evidence, model fitting, or certification. Python standard library only; pytest required for tests.

From project root:

```powershell
python -m pytest -q tests/test_s821_capture.py
python research/p0_s8/s8_21/run_s8_21.py --project-root . --demo
```

`--demo` appends **four synthetic events each run** to `artifacts/capture_ledger.sqlite3`: two new unique payloads on first run, one duplicate, one simulated failure. Re-running will record additional duplicate events. `artifacts/blobs/<sha256>.bin` stores content-addressed bytes and refuses to overwrite corrupted existing blobs. `artifacts/results/` contains `s8_21_health_report.json` and `s8_21_capture_ledger.csv`. Do not Git-commit `artifacts/` or infer historical pregame validity from demo timestamps.

Implementation uses SQLite append-only **application behavior**, not a tamper-proof database. Later milestones need OS-level permissions, backups, scheduled live adapters, and independently reviewed player eligibility.
