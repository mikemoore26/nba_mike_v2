# NEXT AGENT HANDOFF — P0-S3 S8

## Project
NBA_MIKE v2

## Current phase
P0-S3 — Canonical Data Architecture & Dataset Contract

## Completed before S8
- S1 canonical architecture/contracts
- S2 storage/manifest
- S3 canonical identity
- S4 schema/provenance
- S5 canonical dataset builder
- S6 reproducible D-1 point-in-time snapshots
- INFRA-01 packaging/execution
- S7 leakage/invariant suite

## S8 implementation
Historical Reconstruction Sample is prepared for three established season anchors:
- 2019-20
- 2023-24
- 2025-26

The runner retrieves real regular-season PlayerGameLogs, chooses a deterministic internal target date, reconstructs statistical state through D-1, audits D-1 vs D deltas, and checks deterministic rebuilds.

## Governing historical rule
For target date D, statistical information is eligible only through D-1. Same-day earlier-game information is intentionally excluded.

## Still unresolved / quarantined
- exact intraday injury history
- confirmed lineup publication history
- news timestamps
- historical sportsbook props/odds/line movement
- authoritative rotation/stint truth where ambiguous

## Prohibitions
- Do not train predictive models.
- Do not build betting/ticket logic.
- Do not call intraday historical data solved.
- Do not silently substitute a source when NBA Stats retrieval fails.
- Do not weaken D-1 to make a test pass.

## Next task after S8 passes and is committed
P0-S3 S9 — Closeout: consolidate findings, unresolved risks, acceptance evidence, development journal, handoff, and Git state before deciding whether the phase gate can close.
