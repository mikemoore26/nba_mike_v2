# S7.39 — Offline transaction-statement review

Run `python research/p0_s4/s7_39/run_s7_39.py` from project root after S7.38. Uses S7.38 CSV and SHA256 HTML objects; no network calls. Output `results/s7_39_review.csv` and `results/s7_39_report.json`. Same-sentence matches are review-only, not proof of origin, date, or publication time. Any missing/corrupt source object fails closed.
