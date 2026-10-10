# S8.22.8 — Pregame data feasibility decision

## Purpose
Decide which pre-tipoff data families are supportable before selecting targets or building models. Prior schedule agreement does not establish historical pregame information.

| Domain | Needed evidence | Failure risk | Priority |
|---|---|---|---|
| Player availability | Timestamped historical injury/roster status and eligibility | Post-tipoff DNP leakage; questionable != inactive | P0 |
| Expected minutes | Archived pregame projections or timestamped prior usage and role information | Actual minutes substituted for forecasts | P0 |
| Starting lineups | Timestamped lineup publication before selected cutoff | Late announcement, retrospective lineup | P1 |
| Player opportunity | Lagged minutes, possessions, touches, shots, usage and role; historical IDs | Rolling-window leakage and roster changes | P0 |
| Betting markets | Book, prop, line, price, timestamp and licensing | Closing-line leakage, survivorship, unlicensed scraping | P1 |

## Evaluation gates
1. Legal/terms and cost review, and explicit permission for intended storage and usage.
2. Original evidence bytes + SHA256 + source URL + trustworthy historical publication/observation timestamp.
3. Player/game identity, season and coverage, missingness, and representative out-of-sample dates.
4. Pregame cutoff audit: source observation precedes cutoff, not merely tipoff.
5. Chronological splits, fold-local transformations and baseline feasibility assessed later.

## Decision
No current S8.22.8 manifest row is verified. Do not claim source coverage, historical as-of, completeness, permission, or model readiness. `RESEARCH_ONLY / BLOCK_TRAINING`. No automated collection authorized. Manual evidence investigation is next.
