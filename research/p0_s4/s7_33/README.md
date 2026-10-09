# S7.33 — Offline NBA article relevance audit

From the project root, run `python -m pytest -q` and then `python research/p0_s4/s7_33/run_s7_33.py`.

Reads the S7.32 capture CSV and saved HTML objects and the S7.30 review CSV. No network requests. Outputs `results/s7_33_report.json` and `results/s7_33_review.csv`. The CSV contains excerpts for manual review; a player mention and nearby transaction vocabulary **do not prove a trade or origin team**. Content hash mismatch and missing objects are explicit flags. Never promotes roster evidence or enables training.
