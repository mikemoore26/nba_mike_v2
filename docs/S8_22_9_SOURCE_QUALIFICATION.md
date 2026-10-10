# S8.22.9 — Pregame source qualification decision

## Priority and rationale

1. **NBA official injury reports**: investigate a dated, versioned 2023-11-15 report first. Original timestamp and report edition matter. A present-day archived page is not proof of when a particular status was known. Starting lineup evidence is not implied by injury reports.
2. **SportsDataIO**: commercial inquiry for point-in-time historical injury statuses, lineup projections/confirmations, player game projections, and pricing. The vendor documents these feed types, but that does not demonstrate availability of November 2023 snapshots with original update times. Ask for a *redacted sample* and field-level timestamp semantics before purchase.
3. **BALLDONTLIE**: existing manually authorized historical game and player stats are promising for lagged opportunity. The injuries endpoint shown in documentation does not itself establish historical snapshots. Their odds docs limit historical game odds to newer seasons, while current props do not preserve historical prices; 2023 prop reconstruction is not justified.
4. **Prior-game-only derivation**: expected minutes can be *estimated* from prior finalized games and role/availability data, but not equated to archived commercial projections. Requires DNP eligibility, roster-change, cutoffs, and game finality audits.

## Research citations / vendor references (checked 2026-10-10)

- [BALLDONTLIE NBA API](https://docs.balldontlie.io/) — player stats, injury and odds endpoint limitations.
- [BALLDONTLIE Lab](https://lab.balldontlie.io/docs/api/) — NBA historical player-prop backtests begin 2024–25; not a 2023 prop source.
- [SportsDataIO NBA API](https://sportsdata.io/developers/api-documentation/nba) — injury, projected/confirmed lineups, player-game projection endpoints.
- [SportsDataIO NBA workflow](https://sportsdata.io/developers/workflow-guide/nba) — projected and confirmed lineup publication practices; not a historical archive guarantee.
- [SportsDataIO coverage](https://sportsdata.io/developers/coverages/nba) — injury, lineups, betting feeds.

## Mandatory provider questionnaire

- Do you offer original 2023-11-15 *point-in-time* snapshots, not revised present-day records?
- What do `created_at`, `updated_at`, `published_at`, `effective_at` and capture time mean?
- Can one retrieve all revisions, including superseded injuries and lineup changes?
- What are exact historical start date, teams, player population, missingness, and latency?
- Are archived injury, lineups, projections, and **player props with book/line/price** separately available?
- Are FanDuel and DraftKings included, and can market price be proven before a chosen cutoff?
- What is the historical replay price, usage quota, retention/export permission, and attribution requirement?
- Can you provide a redacted example with timestamp and full revision history?

## Gate to advance

Archive authorized original dated source + receipt (URL, retrieval UTC, SHA256, bytes, license/terms review), verify a concrete pregame cutoff and player eligibility. A sample can justify a *limited proof-of-concept*, not whole-season coverage. **RESEARCH_ONLY / BLOCK_TRAINING** until later gates independently approve.
