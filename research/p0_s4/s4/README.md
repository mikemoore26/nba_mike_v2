# P0-S4 S4 — Minutes / Role / Opportunity Research

Run unit tests and acceptance first. Then run the real-data research runner, which uses nba_api PlayerGameLogs for 2019-20, 2023-24, and 2025-26.

Commands:
- `python -m pytest tests/test_opportunity_features.py -q`
- `python research/p0_s4/s4/run_s4_acceptance.py`
- `python research/p0_s4/s4/run_s4_opportunity_research.py`

The real-data runner may take time and requires network/API access.
