# NBA_MIKE v2 — S8.22.10.31 adapter contract

## Evidence from preceding milestone
S8.22.10.30: user reported seven synthetic integration tests passed on Windows Python 3.13.15, committed and pushed `5aa18df` on `main`. This does not certify any historical availability, model OOS quality, odds, or real-money betting.

## S8.22.10.31 implementation
A dedicated, importable adapter (`src/nba_mike/adapters/canonical_snapshot.py`) validates the canonical CSV and its parent manifest and translates into the existing D-1 snapshot interface. It uses a strict schema, explicit field map, SHA-256 verification, manifest path/row-count checks, numeric range checks, unique keys, opponent consistency, and D-1 boundary/metadata invariants. Does not overwrite any canonical or snapshot data.

## Test coverage
12 synthetic tests: successful conversion and cutoff, parent tampering, manifest path mismatch, row-count mismatch, invalid numeric/date/team values, duplicate player-game, blocked manifest, and outside-root rejection. Locally 12 passed against uploaded source copies. Actual-repository test status pending user run.

## Research decision
RESEARCH_ONLY / BLOCK_TRAINING / REAL-MONEY DENIED. The adapter does not make historical outcome data valid pregame features, certify injury availability, or validate a betting strategy.

## Next
Run test in repository, review integration with current branch, then consider explicit as-of availability/provenance gates and separate historical outcomes from pregame feature snapshots. Do not treat passing adapter tests as authorization to train.
