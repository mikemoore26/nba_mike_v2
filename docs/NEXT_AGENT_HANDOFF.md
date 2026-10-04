# NEXT AGENT HANDOFF — P0-S3 S1

## Project
NBA_MIKE v2

## Current phase
P0-S3 — Canonical Data Architecture & Dataset Contract

## Completed
- P0-S1 research governance/project charter.
- P0-S2 target/data feasibility research and POCs.
- P0-S3 S1 design package prepared:
  - canonical layered architecture
  - canonical dataset contract
  - P0-S3 milestone plan

## Governing historical rule
For initial statistical reconstruction of a game on date D, use statistical information through D-1. Do not silently introduce same-day information.

## Important unresolved domains
- exact intraday injury history
- confirmed lineup publication history
- news timestamps
- historical sportsbook props/odds/line movement
- reliable complete rotation/stint truth where reconstruction is ambiguous

## Architecture decision
raw -> validated -> canonical -> snapshots -> features/targets -> predictions -> decisions

Raw is immutable. Canonical data is source-independent. Features and targets remain logically separated.

## Current milestone status
P0-S3 S1 is complete only after installation checks and Git checkpoint pass.

## Exact next task
P0-S3 S2 — Storage & Manifest Standard.

Define:
1. physical directory contract
2. preferred persistent file formats
3. raw filename convention
4. manifest schema
5. checksums/hashes
6. cache semantics
7. source request metadata
8. rebuild/replay rules
9. retention policy
10. quarantine behavior

## Prohibitions
- Do not train predictive models.
- Do not build ticket/parlay logic.
- Do not call intraday historical data solved.
- Do not silently substitute sources.
- Do not weaken leakage boundaries for convenience.
