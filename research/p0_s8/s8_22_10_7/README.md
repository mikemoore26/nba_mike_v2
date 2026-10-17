# S8.22.10.7 — Provisional Game IDs and Human Review

Read-only staging of the prior eight NBA game-ID hypotheses alongside corrected 2023-11-15 away@home orientations. Two November 16 games remain out-of-scope and have no IDs assigned.

## Run

```powershell
python -m pytest .\tests\test_s822107_crosswalk.py -q
python .\research\p0_s8\s8_22_10_7\run_s8_22_10_7.py --project-root .
```

Optional `--schedule`, `--ledger`, and `--output` support explicit paths. Default input discovery fails if multiple candidate directories exist.

Outputs: `provisional_game_id_crosswalk.csv`, `player_and_team_manual_review.csv`, and `review.json`.

## Review protocol

- Do not edit historical evidence or original S8.22.10.5/6 output.
- For each game ID, manually consult an independently archived NBA game page or official game record, record exact URL, content hash, reviewer, review timestamp, and decision in a **separate working copy** of the crosswalk. Do not mark verified from numeric game ID sequence.
- For each player/team notice, visually inspect the archived PDF page, row and columns, record reviewer and evidence, and preserve unresolved cases. A matched game ID does not verify a player or injury status.
- This stage does not validate injury-report historical availability, publication timestamps, eligibility, or DNP population.
- No training, bets, or automatic approval. `RESEARCH_ONLY / BLOCK_TRAINING`.
