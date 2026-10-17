# S8.22.10.19 — Coordinate-aware name matching

Read-only repair of local PDF excerpt comparison. Strip numeric `x:` prefixes at pipe-token boundaries; reconstruct text; require contiguous normalized tokens. For comma-separated names, also test given-first order. Do not use fuzzy matches or match tokens separated by unrelated words.

```powershell
python -m pytest .\tests\test_s8221019_name_repair.py -q
python .\research\p0_s8\s8_22_10_19\run_s8_22_10_19.py --project-root .
python .\research\p0_s8\s8_22_10_19\append_docs.py --project-root .
```

Outputs: `results/2023-11-15/<digest>/name_corroboration.csv` and `review.json`. All certification fields remain NO; `BLOCK_TRAINING` unchanged. Requires the exact original ledger and S8.22.10.18 diagnostic CSV.
