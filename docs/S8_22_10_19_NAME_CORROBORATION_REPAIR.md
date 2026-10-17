# S8.22.10.19 — Local PDF Name Matching Repair

**Purpose:** Correct false negatives caused by PDF coordinate prefixes and pipe delimiters. Read-only, deterministic token comparisons; no fuzzy matching or inference from nearby names.

**Input provenance:** Original 54-row ledger and S8.22.10.18 44-row diagnostic, both checked against known SHA-256 digests. Reject changed inputs and duplicate IDs.

**Outputs:** 44-row local corroboration table and report. Original excerpts retained in output. No original source files modified.

**Limitations:** Local corroboration does not establish an authoritative NBA player ID, injury status, report publication time, or model-training eligibility.

**Gate:** `RESEARCH_ONLY / BLOCK_TRAINING`.
