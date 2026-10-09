# S8.22 — Manual NBA schedule collector

## Objective
Build the first bounded real-source adapter on S8.21 storage, with an offline fixture and explicit opt-in live retrieval.

## Contract
- Source candidate: NBA CDN scheduleLeagueV2_1 JSON. Endpoint availability and permission must be reviewed in the local environment before live use.
- No automated polling; no fallback scraping or endpoint rotation.
- HTTP request limited to one allowlisted HTTPS URL, 15-second timeout, 3 MB maximum.
- Raw response is preserved in S8.21 *before* parsing. Failure attempts are ledgered.
- Strict schema: leagueSchedule.gameDates[].games[]; ten-digit gameId, UTC-aware gameDateTimeUTC, distinct three-letter team tricodes. Duplicate IDs and malformed values fail closed.
- Response headers (date, content-type, etag, last-modified, content-length, cache-control) are preserved in a separate per-event receipt. They are not independent as-of evidence.
- Per-run CSV is latest-run only; ledger and event-named receipts are retained. Protect both with backups/permissions before operational use.
- Fixture run is a synthetic game, not a real historical observation.

## Caveats
This does not certify game completeness, game status semantics, injury status, roster/eligibility, market access, historical publication, or training readiness. S8.13 boundary remains blocked. The 88 restart games remain separately blocked. The collector records requested checkpoint labels but does not yet validate actual timing relative to tipoff. No automatic scheduling.

## Tests
14 offline unit/integration tests covering valid fixture, invalid JSON, schema drift, bad IDs, duplicate games, missing timezone, invalid teams, duplicate captures, malformed payload preservation, failed retrieval, simulated live success/error, URL allowlist, and mode selection.
