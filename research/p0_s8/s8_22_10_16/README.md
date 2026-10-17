# S8.22.10.16 — Date-aware team-submission classification

Offline, fail-closed research milestone. Consumes the S8.22.10.15 report and four-row mapping exception analysis; does not fetch new game dates or change the 54-row source ledger. Only classifies the four **TEAM_SUBMISSION** records. An out-of-slate matchup is **not** proof of a different game date.

Run from project root:

```powershell
python -m pytest .\tests\test_s8221016_date_scope.py -q
python .\research\p0_s8\s8_22_10_16\run_s8_22_10_16.py --project-root .
python .\research\p0_s8\s8_22_10_16\append_docs.py --project-root .
```

Outputs: `results/2023-11-15/<evidence-fingerprint>/review.json` and `team_notice_date_scope.csv`. Original evidence remains untouched. If the upstream report is ambiguous, use `--report` with the explicit S8.22.10.15 `review.json` path inside the project. Do not use this output for training, historical injury statuses, or as-of availability claims.
