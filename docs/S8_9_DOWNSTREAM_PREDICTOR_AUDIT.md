# S8.9 — Downstream predictor leakage audit

## Motivation
S8.8 passed 14 synthetic feature-invariance checks for opportunity and adaptive-form builders. Those tests did **not** prove downstream exclusion of `target_minutes`, realized `min`, `pts`, `reb`, `ast`, `fg3m`, or safe fold-local preprocessing. Adaptive-form outputs can retain supplied realized columns.

## Scope
This milestone adds a read-only AST/text scanner and explicit predictor-list contract unit tests. It identifies feature-builder calls, model `.fit(...)` sites, predictor selectors, split/CV, preprocessing/calibration constructs, and references to realized outcomes. All findings require human review. It does not execute the project training pipeline or prove variable-level lineage.

## Review procedure
1. Run S8.9 and inspect `s8_9_findings.csv`, prioritizing `MODEL_FIT`, `PREDICTOR_SELECTION`, `OUTCOME_COLUMN_REFERENCE`, `PREPROCESSING_OR_CALIBRATION`, `SPLIT_OR_CV`.
2. Inspect full source and tests for each relevant call site; document exact feature lists and exclusion rules.
3. Confirm all transforms, hyperparameter selection and calibration are fitted inside chronological training folds, with held-out future data unseen.
4. Add runtime fail-closed predictor checks only after locating and reviewing the actual training matrix assembly boundary.
5. Retain pregame-universe, as-of publication, DNP, and 88 restart-calendar blockers.

## Governance
`RESEARCH_ONLY / BLOCK_TRAINING`. A clean report is **not** clearance for model training, promotion, or betting.
