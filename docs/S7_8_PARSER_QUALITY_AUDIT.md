# S7.8 — Injury parser quality audit

**Decision gate: BLOCK_TRAINING.** This milestone measures disagreements and missingness without changing parser extraction or authorization.

Inputs: same-source SHA-256 S7.4/S7.6/S7.7 CSVs. Compare by `(source_page, normalized player name)` where possible. Missing baseline matches are reported as NO_MATCH, not counted as correctness or error. Team–matchup checks use a static NBA abbreviation map; they are consistency checks, not official roster validation. Same-page duplicate players and status disagreements are high-priority. Sample is prioritized and spread across pages.

**Limitations:** 50 orphan continuations were reported by S7.7 but raw orphan text was not persisted; S7.8 cannot determine their causes from CSVs alone. A future parser instrumentation step must export safe, provenance-rich orphan diagnostics. Publication-time verification remains unresolved; historical-as-of eligibility stays false. The parser may misassign fields while still agreeing with itself. Do not use this output as training labels.
