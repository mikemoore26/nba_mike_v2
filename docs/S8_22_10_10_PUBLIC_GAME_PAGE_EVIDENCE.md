# S8.22.10.10 — Public NBA Game Page Evidence

## Objective

Recover from the NBA CDN HTTP 403 by attempting to archive official `www.nba.com/game/` HTML pages for eight provisional 2023-11-15 game IDs. The user previously confirmed HTTP 200 for the public NBA page, but this is not guaranteed for automated GET requests.

## Controls

- No rewriting S8.22.10.7 crosswalk, original PDF, prior archives, or manual review ledgers.
- Capture immutable HTML bytes and SHA-256 receipt; fail on existing receipt mismatch.
- Page title must contain both full team names and the local date. UTC 'GAME INFO' can be next calendar day and is not used as the local date.
- A URL containing a game ID is **circular evidence** for that ID. Page title checks do not independently certify NBA game IDs; no automatic promotion.
- `FETCH_FAILED`, `TEAM_TITLE_MISMATCH`, `DATE_TITLE_NOT_CONFIRMED`, and `MISSING_TITLE` remain unresolved. Manual source inspection and independent schedule/ID corroboration are needed.
- Historical as-of availability, injury publication timing, player identity, eligibility, DNP, and leakage remain unverified.
- Governance: `RESEARCH_ONLY / BLOCK_TRAINING`.

## Next gate

Review archived official page, obtain independent ID/date/team source (e.g. official schedule listing) with citation and hash, and reconcile 54 manual injury-report rows. Preserve evidence separately from derived results.
