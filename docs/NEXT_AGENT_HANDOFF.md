# NEXT AGENT HANDOFF — P0-S3 S3

## Project
NBA_MIKE v2

## Current phase
P0-S3 — Canonical Data Architecture & Dataset Contract

## Completed
- P0-S1 research governance/project charter.
- P0-S2 target/data feasibility POCs and conservative D-1 historical boundary.
- P0-S3 S1 canonical layered architecture and dataset contract.
- P0-S3 S2 storage/manifest standard with immutable raw evidence, SHA-256 integrity, validation/quarantine state, and replay semantics.
- P0-S3 S3 canonical identity implementation prepared: project-owned player/team/game IDs, exact source mappings, fail-closed conflicts, aliases, effective-dated team membership, player-game keys, JSON replay, tests, and acceptance runner.

## Governing historical rule
For initial statistical reconstruction of game date D, use statistical information through D-1. Same-day information remains excluded unless a later timestamp-safe standard explicitly proves eligibility.

## Identity rules
- Names are never primary keys.
- Source IDs are mappings, not universal canonical IDs.
- Established source mappings cannot be silently remapped.
- Player identity survives team changes/trades.
- Ambiguous aliases remain ambiguous; do not guess.
- Canonical player-game grain uses (`game_id`, `player_id`).

## Storage architecture
raw -> validated -> canonical -> snapshots -> features/targets -> predictions -> decisions

## Unresolved domains
- source-specific schema enforcement and field-level validation
- authoritative historical transaction/membership timing at finer granularity
- exact intraday injury history
- confirmed lineup publication history
- news timestamps
- historical sportsbook props/odds/line movement
- authoritative complete rotation/stint history where evidence is ambiguous

## Exact next task
P0-S3 S4 — Schema Validation & Provenance.
Implement source/dataset schema contracts, required columns/types, null/range rules, validation reports, quarantine/fail behavior, and provenance linkage to storage manifests and canonical identity.

## Communication requirement
Maintain `docs/DEVELOPMENT_JOURNAL.md` and replace this living `docs/NEXT_AGENT_HANDOFF.md` at each stable milestone. The requested progress-email system for journal/handoff updates still needs to be implemented in NBA_MIKE v2; do not claim emails were sent until that subsystem exists and is tested.

## Prohibitions
- Do not train predictive models.
- Do not build ticket/parlay logic.
- Do not call intraday historical data solved.
- Do not silently substitute sources.
- Do not merge identities by name alone.
- Do not mutate raw evidence to make validation pass.
