# S8.22.7.4 — Date-level completeness audit

## Purpose
Independently compare a curated NBA date-level schedule with per-game NBA source evidence, without confusing agreement with proven complete coverage.

## Evidence protocol
- Use S8.22.7.2 to archive a **date-level** NBA schedule page with SHA-256 and UTC retrieval timestamp.
- Manually transcribe rows from that page, not from BALLDONTLIE or S8.22.7.3.
- S8.22.7.4 checks receipt hash/size, official host, game IDs observable in archived bytes, unique IDs, teams, UTC tipoffs (5-minute tolerance), and missing/extra games.
- Every report explicitly remains `date_completeness=NOT_CERTIFIED`. This is an evidence review, not proof of complete historical coverage.
- No-game days require a separate independent negative-evidence protocol.

## Open gates
Official date-level source interpretation, date coverage, retrospective as-of availability, pregame player universe, DNP, leakage, chronological splits, fold-local preprocessing, and market validation. No routine collection or training approval.
