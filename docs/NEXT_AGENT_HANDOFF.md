# NEXT AGENT HANDOFF — P0-S3 S2

## Project
NBA_MIKE v2

## Current phase
P0-S3 — Canonical Data Architecture & Dataset Contract

## Completed
- P0-S1 research governance/project charter.
- P0-S2 target/data feasibility POCs and D-1 historical boundary.
- P0-S3 S1 canonical layered architecture and dataset contract.
- P0-S3 S2 storage/manifest implementation prepared: directory contract, immutable raw evidence, JSON manifests, SHA-256 integrity, validation/quarantine state, cache separation, and acceptance tests.

## Governing historical rule
For initial statistical reconstruction of game date D, use statistical information through D-1. Same-day information remains excluded unless a later timestamp-safe standard explicitly proves eligibility.

## Storage architecture
raw -> validated -> canonical -> snapshots -> features/targets -> predictions -> decisions

Raw evidence is immutable. Cache is disposable. Manifests preserve provenance and hashes. Unknown timestamps remain unknown/null.

## Unresolved domains
- exact intraday injury history
- confirmed lineup publication history
- news timestamps
- historical sportsbook props/odds/line movement
- authoritative complete rotation/stint history where evidence is ambiguous

## Exact next task
P0-S3 S3 — Canonical Identity System.
Define stable player/team/game IDs, source-ID mappings, identity conflict handling, trade/team membership semantics, and tests preventing accidental identity drift.

## Prohibitions
- Do not train predictive models.
- Do not build ticket/parlay logic.
- Do not call intraday historical data solved.
- Do not silently substitute sources.
- Do not mutate raw evidence to make validation pass.
