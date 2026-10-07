# NBA_MIKE v2 — Minutes / Role / Opportunity Research Standard

## Why minutes are upstream
Counting-stat opportunity depends strongly on court time. NBA_MIKE should not treat a player's scoring/rebounding/assist history as independent of the opportunity to play.

Concept:
availability -> minutes -> role/usage/opportunity -> per-opportunity production -> stat distribution.

## S4 research scope
S4 creates descriptive, leakage-safe research signals. It is not a production model and does not unlock betting decisions.

## Leakage rule
For each player-game, rolling and expanding histories are shifted by one player-game. For game date D, statistical history remains governed by D-1. Same-game realized minutes and stats are targets/outcomes only.

## Initial minutes signals
- prior-game minutes
- last-3 average and volatility
- last-5 average and volatility
- last-10 average and volatility
- season-to-date average and volatility
- recent-vs-season minutes delta
- role-change flag

The 6-minute role-change threshold is a research heuristic, not basketball truth. It must be evaluated and may later change.

## Production normalized by opportunity
S4 also creates prior-only rolling per-minute rates for points, rebounds, assists, and 3PM. These are research features, not final expected-stat formulas.

## Cold-start behavior
A player's first governed row has no historical feature values. NBA_MIKE must preserve that cold-start uncertainty rather than fill it with future information.

Later work may test hierarchical fallbacks such as player archetype/team/league priors, but they require separate governance.

## Evaluation
The real-data S4 runner compares simple minutes signals using MAE over players with at least five prior games. It reports season-specific results and separates role-change/stable row counts.

This is descriptive baseline research. The best simple signal is not automatically selected as a production model and is not evidence of betting edge.

## Seasons
Initial real-data research anchors:
- 2019-20
- 2023-24
- 2025-26

These intentionally span different NBA periods and match prior feasibility anchors.

## Limitations
Historical injuries and exact confirmed lineups remain unresolved. Therefore S4 cannot claim to know the full causal reason for a minutes change. It measures observable historical role/opportunity behavior under the D-1 contract.
