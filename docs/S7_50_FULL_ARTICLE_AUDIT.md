# S7.50 — Full-Article Evidence and Mapping Audit

## Problem
S7.49 assessed upstream 450-character excerpts and flagged four mapping issues. That can miss claim language outside excerpts.

## Method
Read S7.49 review and S7.46 archive manifest; require local saved archive bytes and SHA-256 match; cross-check exact original URL when manifest available; parse JSON-LD, title/heading, meta and paragraphs; exclude nav/header/footer/scripts; preserve full selected evidence (max 30,000 characters). Apply conservative grammatical direction matching and stage labels. Audit incomplete mappings without guessing team codes from slugs. Report unique SHA-verified object counts separately from review-row counts. Never promote as-of eligibility.

## Known limits
Archive replay content and JSON-LD can be injected, modified, or syndicated. Extracted direction is not proof of completion, transaction date, independent publication, or pre-cutoff availability. Multiple players or captures of one article are not independent reports. Source-independent validation is future work.
