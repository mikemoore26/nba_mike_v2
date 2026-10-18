# S8.22.10.31 — Canonical-to-D-1 adapter contract

## Purpose
Formalizes the column mapping between the governed canonical player-game CSV and D-1 snapshot builder. Existing production builders remain untouched. No API calls, model training, betting recommendations, or real data certification.

## Use
Import `adapt_canonical_rows` from `nba_mike.adapters.canonical_snapshot`. Pass `project_root`, `canonical_path`, `canonical_manifest_path`, and `target_game_date` (ISO YYYY-MM-DD). Optional `expected_entities` and `code_git_commit`. Returns `(rows, metadata)` in memory. Does not write a snapshot.

## Contract
- Requires a canonical player-game-box manifest with `validation_status=PASS`, matching relative artifact path, SHA-256 and row count.
- Requires exact canonical schema and nonblank fields; numeric fields must be finite and nonnegative; minutes <=60.
- Maps `game_date->event_date`, `minutes->min`, `points->pts`, `rebounds->reb`, `assists->ast`, `three_pointers_made->fg3m`.
- Rejects duplicate player-game keys, invalid dates, same team/opponent, malformed inputs, and paths outside the project root.
- Calls existing snapshot builder and verifies D-1 boundary and snapshot metadata.
- Outputs remain `RESEARCH_ONLY`, `BLOCK_TRAINING`, and `DENIED` for real-money approval.

## Important limitation
The canonical file contains **realized game outcomes**, not pregame data. Filtering by event date is not proof that data were published or available as of the cutoff. No historical injury, lineup, market, or as-of certification is supplied. The adapter is not an authorized production forecasting input.

## Tests
`python -m pytest tests/test_s8221031_adapter.py -v`

## Verification
The supplied tests were executed in an isolated environment against the uploaded snapshots and provenance/invariants source: 12 passed. Re-run in the actual repository; results are not pre-certified there.
