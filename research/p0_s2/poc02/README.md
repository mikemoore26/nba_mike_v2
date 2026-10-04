# P0-S2 POC-02 — Play-by-Play & Rotation Feasibility

## Goal
Test whether representative historical games expose usable play-by-play structure across multiple eras.

## Tests
- discover a real game ID from each target season
- retrieve PlayByPlayV3
- inspect event schema
- verify period, clock and action fields
- inspect player/person IDs
- count substitution events
- inspect score-state fields
- preserve small samples/schema evidence

## Important limitation
A PASS does **not** mean rotations have been reconstructed correctly. It only means the raw event stream appears sufficient to justify a later reconstruction experiment.

## Seasons
- 2025-26
- 2023-24
- 2019-20

## Output
`research/p0_s2/poc02/results/`

Do not commit generated results until reviewed.
