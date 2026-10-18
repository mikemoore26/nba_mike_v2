# S8.22.10.29 — Controlled existing-suite smoke gate

**Research only.** This patch does not modify NBA_MIKE source modules, train models, call APIs, or place bets.

1. `python -m pytest tests/test_s8221029_smoke.py -q`
2. `python research/p0_s8/s8_22_10_29/run_smoke.py --project-root .` (inventory only)
3. Review the selected tests, then run `python research/p0_s8/s8_22_10_29/run_smoke.py --project-root . --execute`
4. Inspect `research/p0_s8/s8_22_10_29/results/smoke_report.json` and share the report.

The `--execute` flag runs exactly five pre-existing local pytest modules, separately, with a timeout. It does not test live data or establish a complete end-to-end pipeline. The existing tests were reviewed from the supplied source bundle. No real-money approval is possible here.

## Source review caveat

The supplied review ZIP flattened two different `builder.py` files. Their contents were distinguishable, but the bundle did not preserve original directory paths. This patch is applied to the original repository where paths are intact.
