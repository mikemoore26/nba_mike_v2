# S8.22.10.22 — Alternative-source player registry

## Objective
Recover from NBA Stats CommonAllPlayers acquisition timeout / intermittent DNS failures without fabricating official evidence. Preserve original S8.22.10.21 acquisition for later retry.

## Decision
Acquire `nba_api` community-maintained static players list over HTTPS from GitHub Raw. Validate nonempty player rows, unique positive integer IDs, and names. Record source URL, retrieval timestamp, raw hash, transport, source class and mode. An optional local JSON copy is **unverified**, never a verified live capture.

## Evidence boundary
A mutable present-day player directory cannot establish historical team, eligibility or roster membership on November 15, 2023. A generated adapter only supports **name-based candidate reconciliation** in S8.22.10.20. It must not be represented as an official NBA response. Do not certify player IDs from a matching name alone. No model training or betting promotion.

## Acceptance
Run tests; capture source; inspect output classifications; append docs only on successful hash-valid capture. Preserve `RESEARCH_ONLY / BLOCK_TRAINING`. Next: dated historical NBA team/roster and identity corroboration from independent sources, with disambiguation.
