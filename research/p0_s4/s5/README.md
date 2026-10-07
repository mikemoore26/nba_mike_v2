# S5 execution

Install patch at project root. Acceptance: `python research/p0_s4/s5/run_s5_acceptance.py`.
Historical runner: `python research/p0_s4/s5/run_s5.py` (requires working S4 fetcher and nba_api access).
Regression: `python -m pytest -q`.
Inspect results before Git commit. Do not treat exploratory selection as production evidence.
