# S8.7 targeted leakage source trace

**Scope:** six files identified by S8.6, prioritizing 28 medium-priority scanner findings. This patch creates exact local source excerpts, function signatures, and SHA-256 drift checks. It does not infer defects from the presence of postgame fields in target builders.

**Decision:** `RESEARCH_ONLY / BLOCK_TRAINING`. Source trace ≠ leakage certification.

**Next gate:** After source review, create executable mutation invariance tests against actual feature builders with contract-aware fixtures; ensure target-game perturbation cannot change same-game features. Independently establish pregame player universe.
