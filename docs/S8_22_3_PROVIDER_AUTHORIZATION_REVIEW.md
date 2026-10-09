# S8.22.3 — Provider authorization and coverage review

**Decision:** BALLDONTLIE is the preferred *candidate for manual account/terms review*, not an authorized or tested collector. API-Sports NBA is the second candidate. The NBA CDN remains blocked after HTTP 403. Do not retry or circumvent it.

## Evidence reviewed (2026-10-09)

- BALLDONTLIE official docs: https://docs.balldontlie.io/ — NBA Games available on free tier; API key required; 5 requests/min free, ALL-STAR $9.99/month, GOAT $39.99/month; GET /v1/games supports date filters and pagination; response `datetime` is a candidate UTC tipoff field; `id` is a provider-specific ID, **not proven equal to official NBA game ID**. Player injuries, lineups, and player stats are not free-tier features.
- BALLDONTLIE account plans: https://www.balldontlie.io/account/ — verify current entitlements and pricing before committing.
- API-Sports NBA: https://api-sports.io/sports/nba — advertises free 100 requests/day and PRO $15/month. Actual NBA competition/season coverage and plan entitlements require dashboard verification.
- API-Sports terms: https://api-sports.io/terms — warns that competition-specific data availability can vary and free access may change.

## Decisions and unresolved gates

A public documentation page is **not** proof that your use is authorized. User must inspect terms for research, storage, derived works, redistribution, automation, and any betting-related restrictions. No live API calls or account setup are performed by this patch. Do not request or upload API keys. Validate season coverage, timezone, cancellation/postponement behavior, stable game IDs, NBA-ID crosswalk, rate limits, and S8.21 raw-response capture with an explicitly permitted manual call in a future milestone.

Schedule-source gates are distinct from player-eligibility and model-training gates. Historical participant logs remain exploratory; 88 restart games remain separately blocked.
