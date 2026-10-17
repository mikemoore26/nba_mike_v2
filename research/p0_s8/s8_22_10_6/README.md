# S8.22.10.6 — Schedule authority reconciliation

Read-only research patch. Consumes S8.22.10.5 `manual_review_ledger.csv` and produces a unique-matchup reconciliation table and a non-destructive annotated copy of the ledger. No changes to source data or manual decisions. **BLOCK_TRAINING** remains in force.

Evidence: [Basketball-Reference November 2023 schedule](https://www.basketball-reference.com/leagues/NBA_2024_games-november.html) independently lists the eight Nov 15 games and two Nov 16 games. [NBA.com CLE@POR game 0022300199](https://www.nba.com/game/cle-vs-por-0022300199) separately confirms that game. This patch does **not** independently verify the remaining NBA game IDs, historical as-of publication, or player identity.

Commands (project root):

```powershell
python -m pytest .\tests\test_s822106_schedule.py -q
python .\research\p0_s8\s8_22_10_6\run_s8_22_10_6.py --project-root .
```

Inspect `review.json`, `unique_matchup_reconciliation.csv`, and `annotated_review_ledger.csv` under `research/p0_s8/s8_22_10_6/results/2023-11-15/<ledger-hash>/`. The source ledger is never modified. Existing 48 row-level reversal flags are historical comparisons against the *previous* crosswalk, not 48 distinct matchups. Source publication time, DNP/eligibility, and training remain uncertified.
