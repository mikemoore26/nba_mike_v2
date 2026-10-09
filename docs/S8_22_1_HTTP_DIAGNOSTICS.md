# S8.22.1 — HTTP failure diagnostics

## Decision
Correct the missing HTTP status in S8.22 live failures before any additional live collection. Keep `RESEARCH_ONLY / BLOCK_TRAINING`.

## Implementation
- An `HTTPError` now retains its numeric status and a safe allowlist of response headers in both the report and per-event receipt.
- A maximum 2049-byte error-body sample is consumed; only SHA-256, bounded sample length, and truncation flag are recorded. No raw error-body text, cookies, or authentication headers are persisted.
- HTTP 403, 404, 429 and other errors produce an S8.21 `FAILURE` event with no parsed games.
- One manual request only: no retry, bypass, fallback, or endpoint substitution.
- Existing fixture parsing and raw successful-response capture remain unchanged.

## Source evaluation
`https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json` remains an unverified NBA CDN candidate. Do not switch to undocumented endpoints automatically. A 403/429 should stop collection; a 404 should trigger separate source research and permission/schema review.

## Limitation
This patch diagnoses the failed request; it does **not** establish a working authorized NBA source, forward as-of certification, complete eligible-player population, or model readiness.

## Commands
Run `python -m pytest -q tests/test_s822_schedule.py` and then manually run `python research/p0_s8/s8_22/run_s8_22.py --project-root . --live` once. Upload `research/p0_s8/s8_22/results/s8_22_report.json` and the newest `s8_22_receipt_*.json`.
