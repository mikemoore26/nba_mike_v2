# S8.12 — Pipeline boundary mapping

Read-only AST inspection of `src/nba_mike` and `research/p0_s4`. It identifies local call sites and assignment relationships, with special attention to five S8.11 feature-builder call sites. It does **not** execute project code, network calls, training, prediction, preprocessing, or calibration.

From repository root:

```powershell
python -m pytest -q tests/test_s812_pipeline_mapping.py
python .esearch\p0_s8\s8_12un_s8_12.py --project-root .
```

Outputs: `results/s8_12_report.json`, `s8_12_call_sites.csv`, `s8_12_assignment_edges.csv`, `s8_12_priority_paths.csv`. Review source lines and imports manually; assignment edges are syntactic only. Any `.fit` hit is a **candidate**, not proof of training. All training remains blocked.
