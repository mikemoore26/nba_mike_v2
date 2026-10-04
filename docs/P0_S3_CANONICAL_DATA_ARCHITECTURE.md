# NBA_MIKE v2 — P0-S3 Canonical Data Architecture

## Status
DESIGN CONTRACT — no model training is authorized by this document.

## Purpose
P0-S3 converts the feasibility findings from P0-S2 into a reproducible data architecture. The architecture must make leakage, silent source substitution, identity drift, and unreproducible historical features difficult by design.

## Core pipeline
1. `raw` — immutable source responses plus retrieval metadata.
2. `validated` — source-shaped data that has passed schema and integrity checks.
3. `canonical` — NBA_MIKE-standard entities and facts with stable IDs and units.
4. `snapshots` — time-bounded views representing what was allowed at an AS_OF_TIME.
5. `features` — model inputs created only from eligible snapshot data.
6. `targets` — realized outcomes kept logically separate from features.
7. `predictions` — future model outputs, versioned independently from source data.
8. `decisions` — market/edge decisions, never embedded into the performance target.

## Non-negotiable boundaries

### Raw is immutable
Raw responses are evidence. Never silently rewrite a raw file because a parser changed.

### Validation precedes canonicalization
Malformed, incomplete, duplicated, or identity-conflicted source data must be quarantined or fail loudly before it enters canonical tables.

### Canonical data is source-independent
Downstream research should consume NBA_MIKE canonical columns rather than endpoint-specific column names.

### Features and targets are separate
A feature builder may read eligible historical facts and snapshots. It must not read target-day outcomes for the row being predicted.

### D-1 statistical rule
Until a stronger timestamp-safe reconstruction is proven, a game on date D may use statistical aggregates through D-1. Same-day earlier-game information is intentionally excluded.

### Intraday quarantine
Historical injuries, confirmed lineups, news, odds, line movement, and other intraday information remain a separate unresolved domain until their historical publication/availability timestamps are proven.

### Rotation truth
Play-by-play access does not imply trustworthy lineup/stint reconstruction. Ambiguous lineups must remain ambiguous. No guessing to force a complete dataset.

## Proposed project data tree

data/
  raw/
    nba/
  validated/
    nba/
  canonical/
    dimensions/
    facts/
  snapshots/
    pregame/
  features/
  targets/
  quarantine/
  manifests/

artifacts/
  models/
  calibration/
  predictions/
  decisions/

reports/
logs/

## Canonical tables

### dim_players
One canonical record per NBA player identity.

### dim_teams
One canonical record per team identity.

### dim_games
One canonical record per game.

### fact_player_games
One record per player/game. Contains realized game facts only.

### fact_team_games
One record per team/game.

### snapshot_player_pregame
One record per player/game/AS_OF_TIME snapshot. Contains information permitted before prediction.

## Provenance minimum
Every canonical build must be traceable to:
- source name
- source endpoint/dataset
- retrieval timestamp
- source parameters
- source/raw artifact identifier
- canonical schema version
- builder version
- build timestamp

## Failure philosophy
Critical identity, schema, leakage, or completeness failures stop promotion of affected data. A pipeline must not convert ERROR into PASS by silently using a different source.

## P0-S3 exit requirement
P0-S3 is not complete until a sampled player-game dataset can be rebuilt reproducibly from raw inputs, validated against invariants, and shown to respect the historical cutoff contract.
