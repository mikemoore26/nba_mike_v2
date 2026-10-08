# S7.25 — NBA Stats season roster candidate acquisition

Run from project root: `python research/p0_s4/s7_25/run_s7_25.py --team NYK --season 2025-26`.

The official NBA Stats `commonteamroster` endpoint may throttle, block, or change format. Failed retrieval exits nonzero and never fabricates rows. Run one team first; do not hammer the endpoint. For offline reproducibility use `--input-json path/to/response.json` with a previously saved authentic response. Outputs under `results/` include SHA-256 content-addressed original JSON, candidate CSV and report JSON. The JSON is retrieved **now**, not a proven March 2026 historical snapshot.

**Do not copy candidate CSV into S7.23 or S7.24.** A season roster cannot prove team membership on a specific March date. Date-specific transaction/contract evidence is a later milestone. Research-only, training blocked.
