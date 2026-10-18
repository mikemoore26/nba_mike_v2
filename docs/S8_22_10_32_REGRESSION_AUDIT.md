# S8.22.10.32 — Adapter integration and regression audit

## Purpose
Verify the existing canonical builder, the governed canonical-to-D-1 adapter, and the opportunity research feature generator together, using synthetic local data only. No APIs, model training, odds, or real bets.

## Scope
- End-to-end synthetic canonical construction with identity mapping and manifest.
- Adapter enforces verified hash, manifest row count, D-1 date cutoff, metadata, and expected entity history.
- Opportunity research frame derives shifted historical minutes, including same-day isolation.
- Repeated executions are deterministic; tampered artifact/manifest are rejected.
- Journal updates are append-only, idempotent, fail on missing journals, and avoid extra blank lines at EOF.

## Important caveats
- The feature frame includes `target_minutes`, an evaluation label, and **must not** be fed directly into a pregame predictor.
- Prior game dates do not prove that every historical source field was published and available before the target game's decision timestamp.
- Local isolated execution is not certification of the user's full Windows repository. Run both S8.22.10.31 and S8.22.10.32 tests there.
- This patch does not change existing production builders or the adapter.

## Governance
RESEARCH_ONLY / BLOCK_TRAINING / REAL-MONEY DENIED.
