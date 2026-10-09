# S8.18 — Alternative historical evidence source investigation

Scope: game `0022300061`, Lakers at Nuggets, 2023-10-24, scheduled 19:30 ET. Preserve S8.16 official injury PDF SHA256 `126bd5162d1dc4d568a536029fc4fc4a5557ef23ac25652dd706b3d79c8a0e2f` as a reference; do not overwrite it.

Candidate sources (not independently certified):

- Denver Nuggets team pregame preview, publisher label 2023-10-23 20:09 MDT: https://www.nba.com/nuggets/news/nuggets-open-regular-season-with-a-rematch-against-lakers
- NBA opening night rosters, publisher label 2023-10-24 17:03: https://www.nba.com/news/nba-rosters-regular-season-2023-24
- NBA Starting 5 pregame editorial, publisher label 2023-10-24 17:40: https://www.nba.com/news/starting-5-oct-24-2023
- Yahoo/LeBron Wire pregame report, publication date shown without precise time: https://sports.yahoo.com/lakers-vs-nuggets-stream-lineups-160020959.html
- Official 18:30 ET injury-report edition: https://ak-static.cms.nba.com/referee/injury/Injury-Report_2023-10-24_06PM.pdf
- NBA box score (POSTGAME ONLY): https://www.nba.com/game/0022300061/box-score

## Independent verification protocol

1. Retain original bytes, response headers, acquisition time, SHA256.
2. Find third-party archived pregame capture or verifiable timestamped contemporaneous distribution, with original bytes and provenance.
3. Compare captured artifact content against current version and document any later edits.
4. Separate league/team-originated sources from genuinely independent sources; syndicated content may not be independent.
5. Require game-specific eligible population and DNP reconciliation from additional sources. Never infer pregame eligibility from postgame participants.
6. Without credible independent timestamp, classify `HISTORICAL_PUBLICATION_UNVERIFIABLE`; no automatic approval.

**Governance: RESEARCH_ONLY / BLOCK_TRAINING.**
