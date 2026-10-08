# S7.10 — PDF Table Structure Investigation

## Why
S7.9 passed 205 tests but recovered zero context proposals among 32 missing-context records. It captured 84 reason-column trace lines (34 near a player, 50 without a safe anchor). A new extraction heuristic would be premature.

## Scope
- Read official report PDF and matching S7.7 CSV, optionally S7.9 reason traces.
- Generate per-page text/coordinate and token summaries, row-centered nearest context evidence, and optional page PNGs for visual review.
- Preserve original CSV; no automatic assignment or training promotion.

## Evidence rules
Coordinates and nearby text are observations, not proof of team, matchup, date, or reason assignment. Text line grouping can mix multiple PDF columns. PNGs are for visual inspection of merged cells and page transitions. Review outputs before proposing parser changes.

## Acceptance
Run 13 new isolated tests, full suite, and real-PDF audit. Compare page summaries and diagnostics for pages 3–7, then inspect page PNGs. Full-suite target 218 assuming S7.9 baseline 205 and no test changes.

## Known limitations
Source PDF unavailable to the patch author during packaging, so real-document extraction remains unvalidated. PDF filename timestamp does not verify public availability at that time. No record becomes eligible for training.
