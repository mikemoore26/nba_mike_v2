# S7.37 — Controlled official transaction announcement discovery

## Problem
S7.36 classified 114 Bing RSS links; all were external and irrelevant. The captured official NBA trade tracker already embeds direct NBA-hosted article and team announcement links.

## Decision
Extract those links from the immutable S7.27 source HTML; join to S7.30 candidates only where two player-name tokens appear in the link URL or anchor text. Catalog all qualifying official links for later manual/structured review. Do not infer team origins or transaction chronology.

## Acceptance
Source SHA and candidate provenance must match. Link host must be NBA-owned and article path allowlisted. Outputs are review-only. No live article acquisition or historical publication claim. Training stays blocked.

## Next
S7.38 may fetch a small sample of directly matched official articles, save content-addressed copies, and validate player + destination + origin statements with independent review. Historical as-of publication requires separate verification.
