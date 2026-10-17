# S8.22.10.4 — Date-aware injury PDF attribution

Offline, read-only evidence review. Requires `pypdf`; `pytest` for tests. Does not retrieve data, authorize training, certify historical as-of availability, or resolve player identity.

```powershell
python -m pytest .\tests\test_s822104_date_scope.py -q
$Receipt = '.\research\p0_s8\s8_22_10\evidence\2023-11-15\0ed781ec55ef4391a7e6dfdb2f6aff14\receipt.json'
python .\research\p0_s8\s8_22_10_4\run_s8_22_10_4.py --project-root . --receipt $Receipt
```

Outputs under `research/p0_s8/s8_22_10_4/results/2023-11-15/<run-id>/`: `review.json`, `player_status_candidates.csv`, `team_submission_candidates.csv`, `ambiguities.csv`, `out_of_slate_candidates.csv`. Every row is `MANUAL_REVIEW_REQUIRED` and not historically as-of certified. The report edition date and individual game date are distinct. The parser explicitly recognizes page-four table rows at y=90.9 and the 11/16/2023 date transition at y=114; report title and footer are excluded.

The eight-game slate is a narrow 2023-11-15 research scope; November 16 games in the PDF are preserved as out of scope. Reconstructed text is not verified against the original PDF by this step. No original PDF or generated evidence should be committed by default.
