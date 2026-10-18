# S8.22.10.27 — Functional Pipeline Audit (stage 1)

This is a **static, read-only** diagnostic, not a runtime certification. It never imports project modules, loads models, connects to APIs, or executes entry points. It reads project source/config files and writes only its own JSON report under this milestone's `results/` directory. It excludes data/results/artifacts directories from scanning by design; do **not** interpret missing model files as proof that no models exist.

Run from the repository root:

```powershell
python -m pytest tests/test_s8221027_functional_audit.py -q
python research/p0_s8/s8_22_10_27/run_s8_22_10_27.py --project-root .
```

Review `research/p0_s8/s8_22_10_27/results/functional_pipeline_audit.json`. `potential_entrypoints` are AST-based **candidates**, not confirmed runnable commands. Import lists are syntactic references, not dependency-resolution results. Every readiness gate remains NOT_VERIFIED. Do not train models, place bets, or authorize real money based on this report.

Next stage: manually choose a narrow subset of likely production scripts, inspect their input/output contracts and timestamp handling, and create isolated smoke tests. Only after those pass should the runtime pipeline be evaluated.
