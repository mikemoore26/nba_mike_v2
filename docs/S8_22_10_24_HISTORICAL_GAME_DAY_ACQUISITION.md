# S8.22.10.24 — Acquire dated historical NBA boxscore evidence

## Question
Which of the 44 independently name-matched NBA ID candidates can be associated with the teams shown in the injury report using actual November 15, 2023 game-day evidence?

## Source
Third-party ESPN NBA scoreboard (`dates=20231115`) and each returned event's summary endpoint. Raw HTTP JSON is retained byte-for-byte and hashed. The capture manifest records source URLs, retrieval timestamps, and hashes.

## Interpretation limits
- ESPN athlete IDs are distinct from NBA player IDs; name matching is only provisional.
- Boxscore presence is evidence of a listing, **not** definitive date-specific roster membership.
- Boxscore absence is never evidence of absence from a team, particularly for injured/inactive players.
- Games may be missing or endpoint schemas may change; the pipeline fails closed on invalid responses.
- This source cannot certify injury status or publication time of the original injury report.

## Outputs
`results/2023-11-15/<digest>/`: scoreboard JSON, each event summary JSON, boxscore listing JSON, review CSV, and `review.json` with hash/provenance ledger. Review 44 classifications; do not promote certification counts.

## Gate
`RESEARCH_ONLY / BLOCK_TRAINING`. Next: date-specific team roster/transactions plus official historical injury evidence, with cross-source identity reconciliation.
