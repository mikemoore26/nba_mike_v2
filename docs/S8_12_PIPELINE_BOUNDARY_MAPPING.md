# S8.12 — Pipeline architecture and enforcement-point mapping

## Purpose

Advance from S8.11's five candidate research entry points to a reproducible read-only map of call sites, local assignment dependencies and possible fitting/splitting calls. No speculative integration into a training function.

## Interpretation

- `s8_12_priority_paths.csv` shows the five priority pipelines and nearby assignments.
- `s8_12_call_sites.csv` lists AST-discovered calls; `.fit` may be an unrelated object method.
- `s8_12_assignment_edges.csv` lists variable assignments within source, not proven runtime or interprocedural lineage.
- The report records unresolved gates and preserves `BLOCK_TRAINING`.

## Proposed future boundary (not implemented)

Any future central training service must require: independent as-of timestamped data manifest, independently established pregame player population and DNP reconciliation, verified explicit feature allowlist, target/predictor separation, chronological fold boundaries, and fold-local preprocessing/calibration. Reject missing evidence by default. Do not automatically allow training because a static scan is clean.

## Next review

Use the generated call-site and priority-path files to inspect actual downstream consumers. If no real model fitting exists, design the service boundary without fitting models. Separately resolve independent source timestamps and pregame eligibility. The 88 restart-period games remain unverified.
