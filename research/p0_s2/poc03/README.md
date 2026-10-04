# P0-S2 POC-03 — PBP Event Ordering & Substitution Semantics

## Why this exists
POC-02 found usable PBP across 2025-26, 2023-24 and 2019-20, but `actionNumber` was not monotonically increasing. We must understand ordering and substitution records before reconstructing rotations.

## Questions
- Why does `actionNumber` reverse?
- Does `actionId` behave differently?
- Does returned row order preserve period/clock chronology?
- How are substitutions represented?
- What does `personId` mean on substitution rows?
- What values appear in `subType`?
- How common are multiple events at the exact same game clock?
- How are period boundaries and overtime represented?

## Outputs
Generated under `research/p0_s2/poc03/results/`:
- `poc03_summary.txt`
- `poc03_report.json`
- substitution rows for each test game
- local context around substitutions
- same-clock event examples

## Rule
Do not write a rotation reconstruction algorithm until these outputs have been reviewed.
