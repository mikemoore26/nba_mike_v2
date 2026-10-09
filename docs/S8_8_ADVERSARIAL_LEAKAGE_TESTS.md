# S8.8 — Adversarial feature leakage tests

**Research-only, training blocked.** This is an executable behavioral audit of existing S4/S5 feature builders, not a model training or data-certification step.

## Test design

A synthetic two-player dataset contains 12 dates per player plus two same-date player A games. We change the target game's final minutes/box-score stats, future outcomes, and another player's outcomes. Earlier and same-date *non-target* outputs must remain invariant. Input permutation must not alter results. Cold-start historical features must be missing. `target_minutes` must be present while raw `min` must not remain in the returned frame.

The suite intentionally does **not** assert that `target_minutes` is absent from all downstream feature matrices; this requires a separate consumer-level audit. Same-day aggregation of prior-date outcomes may be legitimate, but the test does not certify within-day as-of timing. The snapshot player universe remains postgame-derived and unsuitable for historical pregame selection.

## Governance

A 14/14 PASS only establishes behavior on this synthetic fixture for these two imported functions. No historical source timestamp proof, pregame population, DNP reconciliation, chronological training preprocessing/calibration verification, or 88 restart-game schedule resolution. **RESEARCH_ONLY / BLOCK_TRAINING** regardless of outcome.

## Follow-up

If failures occur, inspect case-level output, create minimal reproduction, then propose a narrowly scoped fix with regression test; no blind repairs. If all pass, move to downstream feature-column/target separation and fold-local validation, and independently resolve player-universe lineage.
