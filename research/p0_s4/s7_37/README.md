# S7.37 — controlled official transaction URL discovery

Run from the project root: `python research/p0_s4/s7_37/run_s7_37.py`.

Reads S7.27 immutable official tracker HTML and S7.30 candidate review. Verifies original SHA-256 and every candidate source SHA. Extracts official `nba.com/news/...` and `nba.com/<team>/news/...` links, conservatively matches player tokens in article URL or anchor text.

Outputs: `results/s7_37_report.json`, `results/s7_37_link_catalog.csv`, `results/s7_37_review.csv`. No network access, no article contents, no transaction verification, no historical publication proof, and **no training promotion**.
