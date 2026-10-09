# S8.0 — NBA Modeling Readiness Audit

## Objective
Inventory local minutes, player-stat, baseline, validation, market, and roster/availability artifacts to plan a source-level audit. This stage does **not** authorize training.

## Classification
- **BLOCKED**: no relevant artifacts found, or chronology-dependent roster/availability sources remain unverified.
- **NEEDS_REPAIR**: candidate files exist, but as-of provenance, actual row-level quality, baseline performance, or chronological evaluation has not been established.
- **READY_FOR_RESEARCH**: reserved for a future milestone after concrete source-level checks; never assigned by this inventory alone.

## Required next gates
1. Establish exact dataset lineage, temporal availability, and permitted cutoffs per feature.
2. Audit row-level IDs, game dates, missingness, duplicates, and leakage.
3. Reproduce chronological out-of-sample minutes and player-stat baselines without unverified roster inputs.
4. Document error buckets, calibration and deployment decisions separately.

## Guardrails
No historical roster/transaction features from S7.51 may be used. A timestamp column name is not evidence of when data became public. `RESEARCH_ONLY / BLOCK_TRAINING` remains in force.
