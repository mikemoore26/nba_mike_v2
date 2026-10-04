# P0-S2 POC-05 — Starter & Period-Start Lineup Feasibility

## Why POC-05 exists

POC-04 showed that substitution identity resolution works, but early-period
player activity is not reliable enough to infer every period's starting five.

POC-05 rejects that assumption and tests a different question:

> Can authoritative game starters seed Q1, and can later period starts be
> solved from the complete substitution sequence as a constraint problem?

## Constraint logic

For every substitution:

- outgoing player must be ON before the event;
- incoming player must be OFF before the event;
- after the event, outgoing becomes OFF;
- incoming becomes ON;
- lineup size remains five.

For a team/period, POC-05 tests every possible five-player starting combination
from players who officially played.

- 0 solutions = inconsistent / data or interpretation problem
- 1 solution = uniquely determined by the substitution chain
- >1 solutions = ambiguous; DO NOT GUESS

## Q1

The official traditional box score is inspected for a starter indicator
(`position` or equivalent). If five official starters are available, POC-05
checks whether they satisfy the substitution constraints.

## Important limitation

A substitution-only constraint solver may still leave later periods ambiguous.
That is a valid result. This experiment exists to determine what additional
source or method is necessary.

## Outputs

`research/p0_s2/poc05/results/`

- `poc05_summary.txt`
- `poc05_report.json`
- period-level solution-count CSVs
- player minute comparisons using only uniquely solved periods

## No production promotion

Even a PASS here does not promote rotation reconstruction. It only determines
whether the approach deserves broader validation.
