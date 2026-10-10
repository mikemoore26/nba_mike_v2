# S8.22.7.8 — Crosswalk governance

**Problem:** Eight official and provider records appeared aligned, but 12+ team IDs lacked independent crosswalk provenance. Matching by row order or by a game-derived crosswalk cannot establish independent identity.

**Decision:** Offline validator checks source capture hash, independent official extraction report, one-to-one matchups, UTC time differences, and mapping provenance labels. Seed a **candidate-only** mapping for the 16 team IDs present in the November 15 schedule. Do not assert the crosswalk has been verified.

**Remaining:** Archive BALLDONTLIE `/v1/teams` response or other genuinely independent authoritative team-ID listing with receipt, verify team IDs from its bytes, and upgrade only validated rows. Independent NBA date completeness and historical pregame availability remain unverified.

**Governance:** RESEARCH_ONLY / BLOCK_TRAINING.
