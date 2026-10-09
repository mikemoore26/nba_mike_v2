# S8.17 — bounded historical archive diagnostics

## Motivation
S8.16 acquired the official NBA PDF (SHA-256 `126bd5162d1dc4d568a536029fc4fc4a5557ef23ac25652dd706b3d79c8a0e2f`), but the CDX response was three bytes and flagged `CDX_SCHEMA_INVALID`. The three bytes may be the valid empty JSON array `[]\n`; inspect preserved raw bytes before assuming schema corruption.

## Approach
Test alternate CDX JSON queries (with/without status filtering), text CDX, and the Wayback availability API; preserve each original response with hashes and never overwrite artifacts. Network access requires `--query-archives`. The prior S8.16 JSON artifacts are independently reclassified without mutation. Capture timestamps from indexes are only candidate evidence and require replay-byte and independent timestamp verification. An empty result means no matching records returned for these queries, not that historical publication was impossible.

## Governance
No verified historical availability, no certified player population, no DNP reconciliation, no approval of 88 restart games. Training blocked. Do not make repeated automated requests if the provider rate limits or errors; review reports and switch evidence strategy.
