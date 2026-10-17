# S8.22.10.16 — Date-aware team notice classification

## Scope

Classify four S8.22.10.15 game-mapping exceptions (T-007 through T-010) as team-submission notices outside the eight-game verified slate, or as extracted-date scope mismatches. Source-extracted dates are not independently authenticated.

## Method

Read the upstream report and exact four exception rows. Check record IDs, `TEAM_SUBMISSION` type, known two matchups (BKN@MIA, OKC@GSW), matching team membership, PDF page/context presence, and upstream fail-closed decision. Emit a source-hash-fingerprinted, non-mutating classification with blank verified game ID and blank corrected date. Fail closed on unexpected input.

## Limitations and next work

No authoritative corrected game date or publisher publication time is inferred. No team submission becomes a player injury. The 44 player injury candidates remain uncertified. Independently investigate source PDF dates and then establish player identity, injury-status provenance, and historical as-of cutoff. `RESEARCH_ONLY / BLOCK_TRAINING` remains mandatory.
