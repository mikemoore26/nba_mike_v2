# S8.22.10.3 — Cross-page PDF attribution (research only)

Requires `pypdf`; tests require `pytest`. The earlier S8.22.10.1 tests additionally require `reportlab` as a test-only dependency.

Run from project root:

```powershell
python -m pytest .\tests\test_s822103_continuation.py -q
$Receipt = '.\research\p0_s8\s8_22_10\evidence\2023-11-15\0ed781ec55ef4391a7e6dfdb2f6aff14\receipt.json'
python .\research\p0_s8\s8_22_10_3\run_s8_22_10_3.py --project-root . --receipt $Receipt
python .\research\p0_s8\s8_22_10_3\append_docs.py --project-root .
```

The source PDF is verified against the S8.22.10 SHA256 receipt. Output is saved in a fresh results directory, not committed by default.

Outputs: `player_status_candidates.csv`, `team_submission_candidates.csv`, `ambiguities.csv`, `out_of_slate_candidates.csv`, `review.json`.

Caveats: the parser uses observed source-specific coordinate bands and approximate vertical association; reasons spanning page boundaries may remain incomplete. Context may be carried across pages only as a **candidate**. It does not verify identity, source publication time, pregame as-of, roster eligibility, or DNP. All rows require manual PDF review. Training remains blocked.
