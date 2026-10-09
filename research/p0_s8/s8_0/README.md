# S8.0 — NBA modeling readiness inventory

Run from repository root:

```powershell
python .\research\p0_s8\s8_0\run_s8_0.py --project-root .
```

This stage is **read-only with respect to project inputs**. It inventories file names and CSV/Parquet schemas and writes three outputs under `research/p0_s8/s8_0/results/`. It does not inspect dataset row values, train models, or claim historical provenance. `READY_FOR_RESEARCH` is deliberately not emitted automatically: filenames and headers alone cannot establish as-of correctness. Any nonblocked component is `NEEDS_REPAIR` pending substantive audit. S7.51 roster/transaction gate remains blocked. Optional `pyarrow` enables Parquet schema inspection; lack of it is reported, not silently accepted.
