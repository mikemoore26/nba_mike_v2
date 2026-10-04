# NBA_MIKE v2 — Storage & Manifest Standard

## Purpose
Make every persistent data artifact traceable, integrity-checkable, replayable, and explicit about validation state.

## Physical directory contract
`data/raw/` immutable source evidence; `data/validated/` source-shaped artifacts that passed checks; `data/canonical/` source-independent tables; `data/snapshots/` AS_OF_TIME/D-1 views; `data/features/` model inputs; `data/targets/` outcomes; `data/quarantine/` rejected/suspicious artifacts; `data/manifests/` machine-readable provenance; `data/cache/` disposable acceleration only.

## Persistent formats
Prefer Parquet for tabular analytical datasets once dependencies are approved. Preserve source-native bytes/formats in raw whenever practical. JSON is the manifest format because it is readable, diffable, and easy to validate. CSV is acceptable for small inspection exports, not the preferred canonical analytical store.

## Raw filename convention
`{source}__{dataset}__{scope}__retrieved-{YYYYMMDDTHHMMSSZ}__{artifact_id}.{ext}`. Never overwrite a prior raw artifact. A repeated request creates a new evidence artifact unless an explicitly verified immutable cached artifact is replayed.

## Manifest minimum contract
Each manifest records: manifest_version, artifact_id, layer, source_name, dataset_name, endpoint, request_parameters, requested_scope, retrieved_at_utc, event_time/published_time/ingested_time when known, as_of_time when applicable, relative_path, media_type, byte_size, row_count when meaningful, sha256, schema_fingerprint when meaningful, request_status, validation_status, quarantine_reason, parent_artifact_ids, code_git_commit, and notes.

Unknown timestamps must be null, never invented.

## Integrity
SHA-256 is calculated from exact artifact bytes. Verification failure is a hard integrity failure. Raw artifacts are immutable evidence: do not silently rewrite them after parsing, cleanup, or schema changes.

## State rules
Allowed validation states: `UNVALIDATED`, `PASS`, `QUARANTINED`, `FAILED`. A raw artifact begins UNVALIDATED. Validation may promote it to PASS or quarantine/fail it. Quarantine preserves evidence and records a reason; it does not erase the original history.

## Cache semantics
Cache is disposable and must never be the sole copy required to reproduce research. Deleting `data/cache/` must not destroy provenance or the ability to rebuild from retained evidence.

## Replay/rebuild
A rebuild should identify inputs by artifact_id + SHA-256, verify hashes before use, preserve parent relationships, record the code Git commit, and emit new downstream artifacts rather than mutating historical evidence.

## Retention
Manifests and raw evidence used by research, validation, paper, candidate, or trusted outputs are retained. Quarantined evidence is retained unless an explicit documented retention decision says otherwise. Cache may be deleted at any time. Large-data archival policy can be revised later without weakening provenance.

## Source substitution
A failed source request is evidence. Do not silently replace a source or endpoint. Any fallback must be explicit in provenance and approved by the source-reliability policy.

## Historical boundary
This standard does not solve intraday history. Initial statistical reconstruction remains D-1 for a game on D until stronger timestamp-safe evidence is proven.
