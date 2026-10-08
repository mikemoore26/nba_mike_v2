# S7.9 — Context evidence and orphan trace

## Purpose

Diagnose 32 records missing dates and associated team/matchup gaps without guessing roster membership or changing the S7.7 parser.

## Safety

- Source PDF hash must match every S7.7 record.
- Only explicit page-local evidence preceding the player is proposed; no cross-page team or matchup inheritance.
- A proposal is always REVIEW_PROPOSAL_NOT_APPLIED; it is never promoted to verified.
- Reason-column traces are not synonymous with true orphans; coordinate proximity is heuristic.
- No model-training eligibility or historical publication verification.

## Acceptance

Run the 12 synthetic tests, full regression suite, and real PDF audit. Compare proposal and trace samples to the PDF visually before any parser change.
