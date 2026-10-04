# NBA_MIKE v2 — P0-S3 Milestone Plan

## P0-S3 objective
Build and prove the canonical data foundation before predictive modeling.

## S1 — Architecture & Dataset Contract
Outputs:
- canonical architecture
- identity/time/data contracts
- storage proposal
- P0-S3 acceptance plan

Pass:
- feature/target boundary explicit
- D-1 rule explicit
- provenance requirements explicit
- unresolved intraday domains quarantined
- no model training

## S2 — Storage & Manifest Standard
Define physical directories, file formats, manifests, naming, hashing, cache policy, and raw immutability.

## S3 — Canonical Identity System
Implement and test game/player/team/player-game keys and joins.

## S4 — Schema Validation & Provenance
Implement schema checks, null/range rules, provenance manifests, quarantine/fail behavior.

## S5 — Source Reliability Layer
Implement caching, retry/backoff, rate limiting, explicit source failures, and no-silent-fallback policy.

## S6 — Canonical Player-Game Builder POC
Construct a small reproducible historical player-game dataset from proven sources.

## S7 — Leakage & Invariant Test Suite
Automate D-1 boundary, key uniqueness, target separation, team/opponent consistency, and provenance checks.

## S8 — Historical Reconstruction Sample
Run across multiple seasons/dates/games and compare repeated builds for reproducibility.

## S9 — Closeout
Update feasibility conclusions, development journal, discovery journal only where scientific findings exist, NEXT_AGENT_HANDOFF, tests, and Git.

## P0-S3 global fail conditions
- hidden source fallback
- target leakage
- name-based identity as primary key
- raw data mutation
- unversioned breaking schema changes
- treating missing as zero without field contract
- pretending intraday historical truth is solved
- training predictive models before the milestone is closed
