# S8.22.10.18 — Investigate 44 uniform name comparison failures

## Objective
Diagnose why S8.22.10.17 reported `NAME_FORMAT_REVIEW` and `SOURCE_EXCERPT_NAME_MISMATCH` for all 44 candidates without assuming that the names are incorrect.

## Controls
- Hash-verifies the original 54-row ledger against its pinned SHA-256.
- Cross-checks all 44 rows against S8.22.10.17 output.
- Diagnoses literal, token-layout, reversed-order, empty-excerpt, and uncorroborated names.
- Produces sample excerpts and row-level CSV for inspection.
- No automatic changes to upstream evidence, no identity/status/as-of certification, no training authorization.

## Follow-up
Use the real diagnostic distribution to decide whether parser logic needs fixing or source evidence is insufficient. Preserve `RESEARCH_ONLY / BLOCK_TRAINING`.
