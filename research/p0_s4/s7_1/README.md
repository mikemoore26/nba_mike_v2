# S7.1 Official injury-report source registry

This is an **offline** registry and provenance gate, not PDF parsing or data ingestion. Three candidate official PDF URLs are included as **references only**, with blank SHA256 and independent availability timestamps. The audit must not label them verified.

Run `python research/p0_s4/s7_1/run_s7_1_acceptance.py`, then `python research/p0_s4/s7_1/run_s7_1.py`, then `python -m pytest -q`.

To advance: retrieve and preserve exact official PDF bytes, document publication and actual availability evidence, parse original pages without treating NOT YET SUBMITTED as Available, resolve player/game IDs, then perform D-1 / pre-tipoff as-of joins. Avoid retroactively inferring first availability from the PDF title.
