# S8.22.10.18 — Name-layout failure diagnostics

Read-only analysis of the 44 player candidate name comparisons from S8.22.10.17. The script does not alter the original source ledger, repair names, certify identities, or unlock training.

Run from project root:

```powershell
python -m pytest .\tests\test_s8221018_name_layout.py -q
python .\research\p0_s8\s8_22_10_18\run_s8_22_10_18.py --project-root .
python .\research\p0_s8\s8_22_10_18\append_docs.py --project-root .
```

Outputs: `results/2023-11-15/<input-hash>/review.json` and `name_layout_diagnostics.csv`.

Interpretation: literal match = exact local excerpt text; token layout = spacing/punctuation discrepancy; reversed = name order discrepancy; empty excerpt = unavailable context; no corroboration = insufficient local evidence. None constitutes authoritative player identity, injury status, or as-of timestamp.
