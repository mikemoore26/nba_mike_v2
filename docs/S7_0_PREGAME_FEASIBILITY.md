# S7.0 Pregame Availability / Rotation — Feasibility Gate

## Why
S6.3 found late-season coverage degradation and concentration of minutes errors among role-changing, volatile, and short-history players. These are associations, not proven injury/rotation causes.

## Decision
**AUDIT ONLY** until historical pregame data can be reconstructed at a declared prediction cutoff. Existing historical game logs reveal participation **after** games, not whether a player was officially available **before** tipoff.

## Data contract
Each prospective observation must carry `source_id`, `game_id`, `player_id`, `field`, `value`, `observed_at_utc`, `available_at_utc`, and `prediction_cutoff_utc`. Reject missing or timezone-naive timestamps; reject publication or availability after cutoff; reject historical revisions without verified as-of revision history. `observed_at` alone does not establish availability to the model.

## Feasibility questions
- Which provider and terms permit historical ingestion and reproducible research?
- Is a timestamped historical archive available, including amendments and late scratches?
- Are game and player identifiers mappable without future information?
- Does the target population include DNPs, inactive players, and nonparticipants? How are scheduled games and active rosters defined at cutoff?
- Can lineup/rotation information be known by cutoff, rather than derived from the actual game?
- Can sources cover both regular season and April without survivorship bias?

## Follow-on gate
S7.1 can implement a *small, source-backed, time-stamped proof of concept* only after a real provider is verified. Until then no model promotion or betting outputs. Holdout contamination from previously inspected 2025-26 persists.
