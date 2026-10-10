# S8.22.7.2 — Independent NBA schedule evidence

## Scope
- Official NBA page archival via opt-in HTTPS or local import.
- Append-only unique evidence folders with SHA-256 and receipt UTC.
- Strict manual normalization with one receipt per reference file.
- Safe manifest update only if target date exists and reference path is blank.
- Fail-closed no-game date handling.

## Acceptance gates
1. Source URL verified as official NBA.
2. Source bytes and SHA-256 preserved.
3. Curator verifies game ID, teams, UTC tipoff, and **complete date coverage**.
4. Distinct evidence for no-game claims.
5. Crosswalk verified; multi-date comparison rerun.
6. Pregame availability and player eligibility remain separate and blocked.

**Warning:** archived contemporary pages do not establish historical as-of availability. Successful candidate matches do not approve routine collection or training.

## Known provider evidence
S8.22.7.1: five provider snapshots; 2, 8, 11, 0, 0 rows. Oct 10 2026 preseason zero is a coverage question, not a verified no-game day.
