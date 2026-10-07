# NBA_MIKE v2 — Target & Outcome Contract

## Purpose
Define exactly what realized player-game outcomes mean before feature research or model training.

## Unit of observation
One target row represents one canonical `(game_id, player_id)` outcome.

Required identity:
- `game_id`
- `event_date`
- `player_id`
- `team_id`

## Initial governed targets
- `target_played`
- `target_minutes`
- `target_points`
- `target_rebounds`
- `target_assists`
- `target_3pm`

These are realized outcomes and must remain logically and physically separate from pregame feature inputs.

## Semantics
`target_minutes` is realized minutes in the target game.
`target_points`, `target_rebounds`, `target_assists`, and `target_3pm` are realized official box-score counting outcomes.

`target_played` is derived from a valid observed outcome row: minutes > 0 => 1, minutes == 0 => 0. It is not permission to fabricate absent/DNP players.

## DNP / absent-player policy
Missing minutes are not converted to zero. An absent or DNP player requires separate availability/roster evidence if the system later wants a true did-not-play target universe.

This distinction matters:
- zero statistical production in a valid observed row is an outcome;
- no trustworthy outcome row is missing evidence;
- missing evidence must not silently become a zero.

## Validity rules
- unique `(game_id, player_id)`;
- valid event date;
- non-null canonical identity;
- minutes >= 0 and <= 60 under the initial plausibility guard;
- counting stats non-negative;
- zero minutes with positive counting stats is impossible and rejected;
- missing realized counting outcomes are rejected.

## Component vs derived targets
Initial governed component outcomes are minutes, points, rebounds, assists, and 3PM.

PRA/PR/PA/RA or market threshold labels should be derived later from governed component outcomes. Do not create separate inconsistent source truths for combinations.

## Leakage boundary
Target values are labels. They cannot be joined into the feature side of the same player-game row. For target game date D, historical statistical feature construction remains D-1 or earlier unless stronger timestamp-safe evidence is proven.

## Scope limitation
This contract does not claim historically complete DNP/availability truth. Injury, confirmed lineup, news, and market timestamps remain quarantined until separately proven.
