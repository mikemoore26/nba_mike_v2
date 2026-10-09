# S8.17 — archive response diagnosis

Research-only, fail-closed. Requires Python standard library; no model training. Run tests first. Offline mode: `python research/p0_s8/s8_17/run_s8_17.py --project-root .`. Network mode (explicit opt-in): `python research/p0_s8/s8_17/run_s8_17.py --project-root . --query-archives`.

Outputs in `results/`: `s8_17_report.json`, `s8_17_request_audit.csv`, `s8_17_capture_candidates.csv`. Raw responses in `artifacts/` are preserved, never overwritten. Existing S8.16 JSON artifacts are hashed and checked for valid empty `[]` responses; no S8.16 files are changed. Archive index candidates are **not** proof of historical public availability. If all methods return empty, record no archived capture found by these methods, **not** proof no capture exists anywhere. `RESEARCH_ONLY / BLOCK_TRAINING` always.
