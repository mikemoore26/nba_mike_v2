# S8.22.10.11 — Independent schedule evidence

Objective: discover NBA game IDs from a date-scoped official NBA schedule page **without consulting provisional game IDs during discovery**. Archive source HTML immutably with a hash receipt; extract only game-page hyperlinks that explicitly encode away team, home team and NBA game ID; compare against the previously generated crosswalk and the S8.22.10.10 game-page title evidence.

## Boundaries

- NBA schedule HTML may be JavaScript-rendered; absence of links is NOT a mismatch or a successful verification.
- A `?date=2023-11-15` request does not itself prove that the returned content is scoped to that date. Human review of schedule date is still necessary.
- Matching schedule anchor IDs and archived page titles are candidate corroboration only; no automatic independent certification.
- Source obtained today does not prove historical pre-tipoff availability.
- All 54 injury PDF review records remain pending.
- `RESEARCH_ONLY / BLOCK_TRAINING` continues.

The report includes HTTP acquisition status, source SHA-256, discovered IDs, mismatches and a candidate review flag. Existing snapshots are never overwritten.
