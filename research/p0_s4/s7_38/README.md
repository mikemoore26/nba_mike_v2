# S7.38 — NBA article content capture and relevance review

From repository root: `python research/p0_s4/s7_38/run_s7_38.py --limit 12`.

Input: S7.37 review CSV (must already exist). Fetch only `OFFICIAL_LINK_REVIEW_ONLY` NBA-hosted article URLs. Restrict redirects and HTML payload size. Save SHA256-addressed raw HTML under `results/objects/`. Output `results/s7_38_review.csv` and `results/s7_38_report.json`. A relevant article is **REVIEW ONLY**; origin team and historical publication remain unverified. Do not promote any evidence or train.
