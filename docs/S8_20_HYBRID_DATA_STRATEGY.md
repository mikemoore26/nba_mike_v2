# S8.20 — Historical Data Strategy Redesign

## Decision
Adopt a **hybrid architecture**: historical game logs and S8.14–S8.19 evidence remain isolated in an **exploratory** partition; a new prospective **forward-capture** partition will eventually record real observations at defined pregame checkpoints. This is a proposed architecture, not an implemented collection service.

## Why
S8.19 confirmed hashes for two artifacts but zero independent historical pregame captures. More historical article-by-article investigation has diminishing returns. Capturing original responses in real time before tipoff creates auditable retrieval-time evidence going forward, though source validity, game eligibility, and independent review remain separate requirements.

## Design principles
1. Append-only original bytes, SHA-256, retrieval UTC, source URL, HTTP status and response headers; never overwrite.
2. Capture source edition timestamp as a **claim**, separate from observed retrieval UTC.
3. Proposed checkpoints T-24h, T-6h, T-90m, T-30m; no schedule or collector is installed in S8.20.
4. Record game IDs, player IDs, team IDs, and missing/incomplete data; never infer pregame eligibility from postgame box scores.
5. Separate retrospective labels and DNP reconciliation from pregame predictors.
6. Market capture requires a permitted data provider and independent provenance.
7. S8.13 fail-closed training authorization remains unchanged; all models blocked.
8. 88 restart-period games remain separately unverified.

## Acceptance gates for a future collector
Successful test fixture with immutable bytes and checksums; replayable timestamp provenance; duplicate and retry semantics; schedule/timezone correctness; player eligibility and DNP reconciliation design; failure/partial-capture handling; privacy/security and rate limits; testable boundary separation; explicit independent audit before any training.

## What this milestone cannot establish
No independently certified historical pregame dataset; no live source connector; no prospective observations; no eligibility reconstruction; no authorization to train or place bets.
