# NBA_MIKE v2 — Canonical Identity Standard

## Purpose
Prevent player, team, and game identity drift before canonical datasets are built. Source names and source IDs are evidence; they are not the project-wide primary key.

## Canonical keys
- Player: `player_id` — stable project-owned ID, format `P########`.
- Team: `team_id` — stable project-owned franchise/team ID, format `T########`.
- Game: `game_id` — stable project-owned game ID, format `G########`.
- Player-game: composite (`game_id`, `player_id`). It is not assigned a second arbitrary ID.

Canonical IDs are immutable once issued. Display names may change without changing identity.

## Source mappings
Every external identity is mapped by (`entity_type`, `source_name`, `source_id`) to one canonical ID. Source IDs are stored as strings so leading zeros and provider-specific formats survive exactly.

A source mapping may not point to two canonical entities. A canonical entity may have many source mappings.

## Names are not keys
Names are descriptive aliases only. Never auto-merge two records because names match. Never auto-split one canonical entity because a display name changes. Name-only resolution must return unresolved or ambiguous unless a separately approved alias rule establishes uniqueness.

## Conflict behavior
The resolver is fail-closed:
- exact source mapping -> RESOLVED;
- no mapping -> UNRESOLVED;
- attempted remap of a source key -> IDENTITY_CONFLICT;
- alias matching multiple entities -> AMBIGUOUS;
- invalid entity references -> FAILED.

Conflicts are evidence. Do not overwrite an old mapping to make a join pass.

## Team membership and trades
Player identity is independent of team membership. A trade changes membership, not `player_id`.

Membership is represented separately with effective intervals:
`player_id`, `team_id`, `valid_from`, `valid_to`, `source/provenance`.

Intervals use half-open semantics `[valid_from, valid_to)`. Overlapping memberships are not automatically rejected because NBA transactions, two-way assignments, corrections, and source timing can be complex; ambiguous membership at an event time must be surfaced rather than guessed.

## Game identity
A canonical game stores scheduled/event date plus home and away canonical team IDs. Source game IDs map to it through the same source-mapping system. Home and away teams must differ.

Do not construct the permanent game key from team names or a mutable schedule string.

## Player-game key
The canonical player-game grain is exactly one row per (`game_id`, `player_id`) for datasets whose contract says one row per player-game. Team at game time is an attribute/reference and must not be embedded into player identity.

## Provenance
Registry serialization must preserve entities, source mappings, aliases, memberships, and schema version. Downstream canonical artifacts should retain the relevant source artifact IDs/manifests separately under the storage/provenance standard.

## Drift protection
The implementation must test:
1. stable ID format and monotonic issuance within a registry;
2. exact source mapping resolution;
3. source-key remap rejection;
4. duplicate source mapping rejection;
5. names not acting as primary keys;
6. ambiguous alias detection;
7. player identity surviving a team change;
8. game home/away integrity;
9. player-game uniqueness helper;
10. registry JSON round-trip without identity change.

## Scope boundary
This stage establishes identity semantics only. It does not prove source truth, historical injury/lineup timestamps, sportsbook history, or predictive value. Do not train models in S3.
