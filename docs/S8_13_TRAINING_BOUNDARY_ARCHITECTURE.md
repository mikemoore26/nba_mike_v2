# S8.13 — Fail-Closed Training Boundary Architecture

## Decision
`RESEARCH_ONLY / BLOCK_TRAINING`. No model training or approval.

## Findings carried from S8.12
131 Python files scanned, 163 call sites, 2,364 local assignment edges; no model-fit, split, or contract call candidates identified in that static scan. These negative matches do not rule out notebooks, dynamic imports, SQL, or external execution.

## Design
- `boundary.py` lists ten independent gates. Evidence metadata is descriptive, not trusted proof.
- `inspect_evidence()` distinguishes missing, unverified and self-claimed evidence, always returning BLOCK_TRAINING.
- `require_training_authorization()` always denies, even if every gate is self-reported VERIFIED.
- `validate_research_inputs()` calls S8.10 predictor and chronology validators for synthetic research-only checks, and cannot grant training authorization.
- No estimator, transformer or calibrator is fitted. No runtime interception of external training code is claimed.

## Future centralized service contract (design only)
Any future training service must own predictor selection, target isolation, population selection, chronological split generation, and fold-local preprocessing and calibration. It must accept independently verified immutable manifests with data hashes, as-of timestamps and audit provenance. There must be no alternate training path. Its implementation requires separate review and tests; it is not implemented here.

## Unresolved
Pregame source publication times; independent player universe and DNP reconciliation; 88 restart games; verified feature lineage; actual training entrypoint; fold-local transform and calibration implementation. The presence of a manifest or a synthetic passing test is not authorization.
