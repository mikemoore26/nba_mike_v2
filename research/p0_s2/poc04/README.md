# P0-S2 POC-04 — Rotation Reconstruction Truth Test

## Goal

Attempt the first derived-data truth test in NBA_MIKE v2.

Use historical play-by-play substitutions plus official game box scores to reconstruct player minutes, then compare reconstructed minutes against official minutes.

## Evidence inherited from POC-03

For substitution rows:

- `personId` / `playerName` identifies the player leaving.
- Description follows `SUB: [incoming] FOR [outgoing]`.
- `subType` is not relied upon.
- `actionId` / returned order is preferred over `actionNumber` for event sequencing.

## Important design rule

The incoming player appears in description text, so POC-04 resolves that name against the official game roster. Ambiguous identities are errors. The program must not guess.

## Starter inference

This POC intentionally tests whether period starters can be inferred from early-period actions and first substitutions.

If a unique five-player starting unit cannot be established for a team/period, that period is flagged rather than guessed.

This is an experiment, not the final production approach.

## Truth-test gates

A game passes only if:

- every incoming substitution is resolved;
- no reconstruction consistency errors occur;
- maximum player minute error is <= 0.25 minutes;
- reconstructed team-player minutes agree with expected team-player minutes within 0.25 minutes.

These thresholds are intentionally strict.

## Expected team-player minutes

- regulation: 5 × 48 = 240 minutes per team
- one overtime: 5 × 53 = 265 minutes per team
- each additional overtime adds 25 team-player minutes

## Outputs

`research/p0_s2/poc04/results/`

Includes:

- `poc04_summary.txt`
- `poc04_report.json`
- one player-level official-vs-reconstructed minute comparison CSV per test season

## Interpretation

PASS means the tested reconstruction approach is promising enough for broader validation.

FAIL does not mean play-by-play is unusable. It means we must identify why reconstruction failed before using rotation-derived features.
