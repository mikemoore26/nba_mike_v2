# S8.22.10.2 — Coordinate-aware NBA injury PDF candidates

Offline, no-network research parser. Requires `pypdf` (runtime) and `pytest` (tests); **no reportlab needed for these tests**.

```powershell
python -m pytest .\tests\test_s822102_layout.py -q
$Receipt = '.\research\p0_s8\s8_22_10\evidence\2023-11-15\0ed781ec55ef4391a7e6dfdb2f6aff14\receipt.json'
python .\research\p0_s8\s8_22_10_2\run_s8_22_10_2.py --project-root . --receipt $Receipt
```

Results are placed in `research/p0_s8/s8_22_10_2/results/2023-11-15/<run-id>/` and contain `player_status_candidates.csv`, `team_submission_candidates.csv`, `ambiguities.csv`, `review.json`.

**Scope and limitations:** Candidate reconstruction from text-matrix positions observed in this PDF; no actual source visual cross-check, historical publication proof, player-identity verification, DNP inference, or training permission. Column and row rules are intentionally specific to the observed edition. Context does not silently carry across page boundaries; these rows are flagged for review. PDF/source hash is checked against original S8.22.10 receipt. All candidates require manual review. Keep evidence and results local; do not stage them by default.
