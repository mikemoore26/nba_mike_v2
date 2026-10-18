# S8.22.10.21 — NBA registry acquisition

## Objective
Capture official NBA Stats `CommonAllPlayers` registry bytes for 2023–24, validate schema and preserve provenance without modifying the historical injury ledger.

## Outputs
- `research/p0_s8/s8_22_10_21/results/2023-24/<sha-prefix>/commonallplayers_raw.json`
- `research/p0_s8/s8_22_10_21/results/2023-24/<sha-prefix>/capture_manifest.json`
- Optional invocation of S8.22.10.20 offline reconciliation.

## Validation
Raw response SHA-256, UTC retrieval time, requested and final URLs, status, row counts, unique IDs, schema, and conflicting ID/name checks. HTTP errors fail closed. No source response is embedded or fabricated.

## Governance
Historical team on game date is unverified; a 2023–24 season filter does not establish that fact. A response captured now does not establish the historical as-of time of a 2023 injury report. No player identity, injury status, or as-of certification is granted. `RESEARCH_ONLY / BLOCK_TRAINING`.
