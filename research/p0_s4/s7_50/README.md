# S7.50 — Full-Article Evidence & Mapping Audit

Offline read-only audit of S7.49 review rows and SHA-verified S7.46 archive objects. Extracts full JSON-LD headline/articleBody/description, metadata, headings, and paragraphs; excludes common navigation/footer content. No network or source mutation.

Run from repository root: `python research/p0_s4/s7_50/run_s7_50.py`. Outputs `results/s7_50_report.json` and `results/s7_50_review.csv`.

Mapping gaps (including Anthony Davis) are **flagged, not filled by guesses**. Full source evidence remains subject to replay contamination, historical timing, and independent corroboration. `RESEARCH_ONLY / BLOCK_TRAINING`.
