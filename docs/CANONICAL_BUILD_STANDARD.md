# NBA_MIKE v2 — Canonical Build Standard

## Purpose
P0-S3 S5 defines the first executable Raw -> Validated -> Canonical boundary. A source-shaped artifact may become canonical only after integrity, schema, identity, and provenance checks pass.

## Fail-closed rules
1. The raw parent artifact must exist and its SHA-256 must match the recorded manifest hash.
2. The parent validation state must be PASS before canonical construction.
3. Source rows must satisfy an explicit schema contract before transformation.
4. Source player/team identifiers must resolve through the canonical identity registry; unresolved or ambiguous identities block publication.
5. Canonical primary keys must be unique. Duplicate player-game rows are rejected.
6. Impossible values are rejected; they are never silently clipped or repaired.
7. A canonical artifact is written as a new immutable downstream artifact. Raw evidence is never rewritten.
8. The canonical manifest records parent artifact IDs and hashes, the code Git commit when available, row count, schema fingerprint, and output SHA-256.
9. Failure produces no trusted canonical output. Rejected build evidence is reported explicitly.

## Initial S5 canonical table
S5 proves the architecture with `player_game_box`, one row per canonical player per canonical game. Required canonical fields are:

- game_id
- game_date
- player_id
- team_id
- opponent_team_id
- minutes
- points
- rebounds
- assists
- three_pointers_made

The implementation is deliberately source-independent: source column mappings are supplied to the builder instead of being hard-coded into the canonical table.

## Time boundary
S5 does not change the P0-S2 research boundary. D-1 remains the conservative reproducible pregame feature boundary. The player-game canonical table is historical outcome evidence and must not be mistaken for a pregame feature snapshot.

## Gate
Passing S5 proves a governed canonical-build mechanism, not production completeness and not predictive value. Predictive model training remains closed.
