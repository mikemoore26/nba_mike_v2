# S8.22.10.15 — Four game-mapping exceptions

## Objective
Determine why four of 54 original injury ledger rows failed game mapping, without editing the source or inventing identity/timing evidence.

## Method
Read S8.22.10.14's 54-row triage and four-row exception queue. Require exact matching IDs, count, and mapping-failure reasons. Compare original date, matchup, and team against the eight automatically verified Nov 15, 2023 games. Offer a deterministic candidate only if the date matches, the team appears in exactly one of those eight games, and there is no conflicting matchup. Otherwise retain manual exception. Output all four row IDs, reasons, source excerpts, and suggested mappings.

## Safety
`DETERMINISTIC_MAPPING_CANDIDATE` is a suggestion, not a corrected source record or certified injury fact. No auto-approval, no altered upstream files, no fabricated historical publication timestamps. `RESEARCH_ONLY / BLOCK_TRAINING` always.

## Follow-up
Use the actual exception analysis to decide which upstream parsing rules can be repaired with evidence and which require new primary-source review. Next, verify player identity, injury status, and historical as-of timing separately.
