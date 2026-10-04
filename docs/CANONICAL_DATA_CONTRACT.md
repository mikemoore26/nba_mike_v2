# NBA_MIKE v2 — Canonical Dataset Contract v0.1

## Contract status
DRAFT / P0-S3.1

This contract defines the minimum structure that later P0-S3 implementation must enforce.

## Identity contracts

### game_key
Canonical: `game_id`

Rules:
- stored as string
- must preserve leading zeroes
- unique in `dim_games`
- never inferred from matchup text when an authoritative game ID exists

### player_key
Canonical: `player_id`

Rules:
- stable numeric NBA identifier stored in a lossless representation
- player name is descriptive, never the primary join key

### team_key
Canonical: `team_id`

Rules:
- stable numeric NBA identifier stored in a lossless representation
- abbreviation/name changes must not create a new identity

### player_game_key
`game_id + player_id`

Must be unique in `fact_player_games`.

### team_game_key
`game_id + team_id`

Must be unique in `fact_team_games`.

### feature_snapshot_key
`game_id + player_id + as_of_time + feature_version`

Must be unique in a feature snapshot dataset.

## Canonical player-game fact schema

Required identity/context fields:
- season
- game_id
- game_date
- player_id
- team_id
- opponent_team_id
- home_away

Required target/fact candidates:
- played
- minutes
- points
- rebounds
- assists
- threes_made
- field_goal_attempts
- three_point_attempts
- free_throw_attempts
- turnovers

Additional fields may be admitted only through schema versioning.

## Pregame snapshot schema

Required metadata:
- season
- game_id
- game_date
- player_id
- team_id
- opponent_team_id
- as_of_time
- cutoff_date
- feature_version
- source_manifest_id
- snapshot_build_time

Initial safe statistical namespace:
- `pregame_*`

Realized outcomes use:
- `target_*`

A production feature matrix must never contain target columns as feature inputs.

## Time contract

For initial historical statistical reconstruction:
`cutoff_date = game_date - 1 calendar day`

This is intentionally conservative.

Later intraday snapshots may use exact timestamps only after source-specific timestamp feasibility is proven.

## Null contract
Null does not automatically mean zero.

Examples:
- missing tracking value != zero touches
- unknown lineup != bench
- missing odds != no market
- unavailable source != zero statistic

Each schema must declare nullable fields and allowed missingness.

## Units contract
Canonical units must be explicit:
- minutes: decimal minutes
- percentages: choose one documented scale per field
- dates: ISO `YYYY-MM-DD`
- timestamps: timezone-aware ISO-8601, UTC preferred for storage
- odds: retain original American odds where sourced; derived probabilities are separate fields

## Data-quality invariants
At minimum:
1. player-game key uniqueness
2. team-game key uniqueness
3. two participating teams per completed NBA game
4. player team belongs to the game
5. opponent differs from team
6. minutes >= 0
7. box-score counting stats >= 0 unless a field explicitly permits another range
8. target fields originate from the target game
9. pregame statistical features do not include target-date game outcomes
10. canonical IDs do not depend on player/team names
11. raw source lineage exists for every canonical build
12. schema version is recorded

## Leakage invariant
For game date D, initial pregame aggregate features must be computed only from eligible events dated <= D-1.

A future feature requiring same-day or intraday information must declare a stronger source-specific AS_OF_TIME contract and pass its own leakage tests.

## Schema evolution
Breaking changes require a new schema version and migration note. Never silently reinterpret an existing column.
