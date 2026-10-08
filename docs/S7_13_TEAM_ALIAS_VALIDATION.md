# S7.13 — NBA team-name normalization

## Issue
S7.12 compared PDF team labels against one canonical string. The report uses `LA Clippers`, while the validator expected `Los Angeles Clippers`. Three LAC@IND player rows were therefore incorrectly flagged.

## Change
Normalize source-document team names to canonical NBA abbreviations before testing matchup membership. Preserve the 30-team mapping, support known aliases, and reject unknown teams. No roster-based inference.

## Validation
Run `run_s7_13_acceptance.py`, full `pytest -q`, then `run_s7_13.py` with the S7.11 candidates and events. Compare flagged counts against S7.12 (3); investigate any remaining flags.

## Governance
Research only; parser assignments still need independent PDF review and multi-document validation. Publication time is not verified. Training remains blocked.
