# NBA_MIKE v2 — P0-S2 Data Feasibility Matrix

**Date:** 2026-10-03  
**Purpose:** Decide what data families deserve controlled proof-of-concept testing before architecture is locked.

## Source policy
NBA_MIKE v2 will not depend on a single provider. A source must be evaluated for:
- historical depth
- current availability
- timestamps / AS_OF_TIME reconstruction
- identifiers
- update frequency
- missingness
- stability
- cost
- access/licensing constraints
- fallback strategy

| Data family | Candidate source(s) | Current finding | AS_OF_TIME potential | Decision |
|---|---|---|---|---|
| Schedules / game IDs | NBA ecosystem; provider API | Strong availability | High | GO_RESEARCH |
| Player box scores | NBA ecosystem; provider API | Deep historical availability | High for completed prior games | GO_RESEARCH |
| Team box scores | NBA ecosystem; provider API | Deep historical availability | High | GO_RESEARCH |
| Player game logs | NBA ecosystem / nba_api reference | Standard fields include MIN/FGA/3PA/FTA/REB/AST/etc. | High for prior games | GO_RESEARCH |
| Play-by-play | NBA endpoints; provider alternatives | NBA endpoint wrappers exist; provider history varies | High for completed prior games | GO_WITH_LIMITATIONS |
| Lineups | NBA lineup history; commercial providers; expected-lineup services | Historical lineup stats exist, but pregame confirmation timing is harder | Medium | INVESTIGATE |
| Rotations / on-court stints | PBP-derived / provider feeds | Likely derivable; needs coverage/quality proof | Medium-High for completed games | INVESTIGATE |
| Tracking: passing | NBA tracking endpoint reference | Passing tracking measure exists | Unknown historical completeness | INVESTIGATE |
| Tracking: rebounding | NBA tracking endpoint reference | Rebounding tracking measure exists | Unknown historical completeness | INVESTIGATE |
| Tracking: drives/touches | NBA tracking endpoint reference | Multiple tracking measures exist | Unknown historical completeness | INVESTIGATE |
| Injuries | Official NBA injury reports; commercial providers | Official reports have defined reporting windows and continual updates | High prospectively; historical archive test required | GO_WITH_LIMITATIONS |
| Expected starters | Commercial/lineup services | Available prospectively, but expected status is provider judgment | High prospectively if snapshotted | GO_WITH_LIMITATIONS |
| Confirmed starters | Official/provider feeds | Confirmation can occur very late | Medium prospectively | GO_WITH_LIMITATIONS |
| Transactions / rosters | Provider APIs / NBA ecosystem | Available, but effective-time history needs testing | Medium-High | INVESTIGATE |
| Game odds | The Odds API; SportsDataIO; others | Historical timestamped markets available from providers | High with paid history | GO_WITH_LIMITATIONS |
| Player props | The Odds API; SportsDataIO; BALLDONTLIE | Historical depth varies materially by provider | High with appropriate provider | GO_WITH_LIMITATIONS |
| Prop line movement | The Odds API snapshots; SportsDataIO Props Plus | Timestamped historical movement available commercially | High | GO_WITH_LIMITATIONS |
| Current FanDuel/DraftKings props | Odds providers | Provider/book coverage must be verified during POC | High prospectively | INVESTIGATE |
| Weather | Not core NBA input | Indoor league; travel/context more important | N/A | DEPRIORITIZE |
| Rest / back-to-back | Derive from schedule | Reconstructable from game schedule | High | GO_RESEARCH |
| Travel / altitude | Derive from schedule + venue metadata | Reconstructable | High | GO_RESEARCH |

## Confirmed source facts from P0-S2 reconnaissance
1. NBA Stats states base stats and box scores extend to 1946-47, advanced stats to 1996-97, and lineup data to 2008.
2. NBA Stats also states its statistics are not offered for download for academic/personal use; therefore NBA.com should not be assumed to be our bulk production data source.
3. `nba_api` is an open-source client around NBA.com endpoints and documents game logs, play-by-play, tracking measure types, player/team IDs, and other endpoint schemas. It inherits NBA.com access/terms/stability concerns.
4. Official NBA injury reporting has scheduled pregame reporting windows and continual updates, making prospective timestamped snapshots attractive.
5. The Odds API documents historical featured-market snapshots from June 2020 and additional markets including player props from May 3, 2023; historical access is paid.
6. SportsDataIO documents projected/confirmed starting lineups, injuries, transactions, game line movement, player props, and prop line movement; NBA access is commercial.
7. BALLDONTLIE documents play-by-play only from the 2025 season. Its current prop endpoint is live and can disappear near game completion, while a separate opening-props endpoint has limited recent-season coverage. It cannot be treated as our sole historical source.

## Architectural consequence
Do not force one universal training start date.

Use data eras, for example:
- CORE_BOX_SCORE_ERA
- MODERN_TRACKING_ERA
- MARKET_GAME_ODDS_ERA
- MARKET_PLAYER_PROP_ERA
- NBA_MIKE_OWN_SNAPSHOT_ERA

Exact boundaries must be measured during proof-of-concept ingestion rather than guessed.

## Key unresolved risks
- historical injury report archive completeness and machine readability
- exact historical availability of tracking categories
- historical expected/confirmed starter timestamps
- stable and permitted bulk source for core historical data
- FanDuel/DraftKings historical coverage by candidate odds provider
- provider cost relative to value
- canonical cross-provider player/game ID mapping
