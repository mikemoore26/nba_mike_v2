# S8.21 — Forward Evidence Capture Infrastructure (offline prototype)

## Decision
Implement a fail-closed, offline-first capture ledger with content-addressed immutable-on-write raw bytes, checksum verification, duplicate event tracking, explicit failed attempts, and checkpoint coverage. Source kinds: schedule, injury_report, roster, starting_lineup, market. Checkpoints: T-24H, T-6H, T-90M, T-30M.

## Evidence boundaries
`received_utc` is the machine's capture time, not a trusted external timestamp; the demo is synthetic and not a historical capture. `publisher_claim` is not independently verified. No live HTTP acquisition, no background scheduler, no certified player universe, no historical backfill, no training or betting. A success event is **not** sufficient evidence of pregame eligibility. The SQLite API is append-only but the file is not tamper-proof.

## Data model
Each event stores an opaque event ID, UTC receipt time, source kind/URL, game ID, checkpoint, outcome, HTTP status, SHA256, blob relative path, duplicate event reference, error code and publisher claim. Payload bytes are content-addressed and stored once. Failed attempts have no blob. Health report lists missing checkpoints and corruption. Demo is safe to run repeatedly but appends more rows.

## Next gate
S8.22: authorized official schedule source adapter; robust response/HTTP provenance, bounded timeouts, retry controls, source-specific schema checks, and a manually triggered test before any automation. Independently assess source terms and game/player eligibility; keep S8.13 gate closed.
