# S8.22.10.30 — Synthetic cross-module integration

Purpose: exercise existing NBA_MIKE v2 components **together**, using synthetic CSV data and temporary directories. No live API, no model fitting, no odds, and no bets.

Run from repository root:

```powershell
python -m pytest tests/test_s8221030_integration.py -q
```

The tests exercise raw CSV + parent hash -> canonical identity mapping -> canonical parent hash -> D-1 snapshot -> leakage and provenance invariants -> opportunity feature generation. The explicit adapter maps `game_date` to `event_date`, and `minutes/points/rebounds/assists/three_pointers_made` to `min/pts/reb/ast/fg3m`. This adapter is deliberately **test-only**; do not treat it as a certified production ETL pipeline.

The opportunity research frame includes `target_minutes` (realized outcome) for diagnostics. It is not a deployable pregame feature frame. The test deliberately proves the target-separation invariant rejects it and that a feature-only view must drop it.

Caveat: A D-1 event-date filter does not prove historical source availability timestamps. Snapshot `as_of_time` is a cutoff label, **not evidence** that the source was available at that time. Passing tests do not certify injury evidence, pregame market data, full-season data, model OOS results, or live betting readiness.

Governance remains: `RESEARCH_ONLY`, `BLOCK_TRAINING`, `REAL_MONEY_DENIED`.
