# S7.2 official injury PDF acquisition — research only

Requires S7.1 `injury_asof.py` and `pip install pymupdf`.

Offline: `python research/p0_s4/s7_2/run_s7_2.py`

Explicit acquisition of one verified official report URL:
`python research/p0_s4/s7_2/run_s7_2.py --url "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-03-27_06_30AM.pdf"`

Or process a manually downloaded PDF, keeping its exact source URL:
`python research/p0_s4/s7_2/run_s7_2.py --url "..." --pdf "C:\path\report.pdf"`

Outputs PDF by SHA256 and `.audit.json` under `results/`. Candidate status lines are NOT parsed player records. No inference of historical public availability. No model training.
