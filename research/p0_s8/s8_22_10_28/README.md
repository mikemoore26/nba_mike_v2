# S8.22.10.28 — Core pipeline contract audit

Static, read-only scan of project Python sources using AST. The only files written are `results/contract_audit.json` and `results/contract_audit.md`. It does not import project code, contact services, run models, or approve betting. Skips `.venv`, `data`, `results`, and generated output folders. Stage assignments and test associations are heuristic. Results may contain source file/function names but no function bodies, data records, or credentials.

From repository root:

```powershell
python -m pytest tests/test_s8221028_contracts.py -q
python research/p0_s8/s8_22_10_28/audit_contracts.py --project-root . --limit 36
Get-Content research/p0_s8/s8_22_10_28/results/contract_audit.md
```

Upload `contract_audit.json` and `contract_audit.md` for manual review of interface compatibility, provenance, and controlled fixture smoke-test selection. This milestone does not change `RESEARCH_ONLY / BLOCK_TRAINING`.
