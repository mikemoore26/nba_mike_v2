# S7.39 — Evidence extraction

Goal: offline, hash-verified sentence-level review of captured S7.38 articles. Exact player name (accent-insensitive) and transaction verb must occur in the same heuristic sentence. All NBA team references are **mentions only**. No inferred trade direction, no independent origin verification, no historical publication evidence, no training promotion. Duplicate matches are retained for manual review.

Run `python -m pytest -q` and `python research/p0_s4/s7_39/run_s7_39.py`. Inspect the CSV for actual quoted evidence, false positives and three-team trade context.
