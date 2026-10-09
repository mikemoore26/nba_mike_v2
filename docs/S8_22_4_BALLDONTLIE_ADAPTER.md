# S8.22.4 — Controlled NBA schedule API adapter

## Objective
Validate one manually authorized BALLDONTLIE NBA Games request using the existing S8.21 capture boundary, without enabling training or unattended polling.

## Architecture
- API key loaded explicitly from project-root `.env` using `python-dotenv` (or an existing process environment variable). No credentials in source code or logs.
- GET `https://api.balldontlie.io/v1/games` with `dates[]` and `per_page=100`, `Authorization` header; 15-second timeout; at most 3 MB response.
- Capture original bytes and request failure into S8.21 **before parsing**. This means invalid JSON is still preserved for investigation.
- Fail closed on non-200 responses, malformed data, duplicate IDs, date mismatches, invalid team IDs and pagination beyond one page.
- Preserve provider game IDs independently; do not fabricate official NBA IDs or missing tipoff times.
- Record limited response headers only; do not preserve the credential.

## Known limitations and gate status
Account permissions and terms are user-verified, not independently certified by this code. No live source approved automatically. Provider fields and date semantics may differ across real responses; inspect report and raw capture if schema rejects them. One-page retrieval only; do not infer full schedule coverage. No official ID crosswalk, pregame player eligibility, injury data, DNP reconciliation, historical as-of certification, or training. The 88 restart-period games remain blocked. `RESEARCH_ONLY / BLOCK_TRAINING` is unconditional.

## Test evidence
15 isolated tests including HTTP 403, network failure, missing key, malformed data, incomplete pagination, valid fixture, and S8.21 ledger integration. Tests do not call the live API.
