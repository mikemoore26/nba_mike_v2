# S7.4 automatic injury parser — research only

This patch replaces the requirement to hand-label every line with automatic candidate extraction. It parses date, matchup, team, player, status and reason, carries context only within a page, and flags unresolved fields.

**Limitations:** PDF text extraction may reorder columns; wrapped reasons can be truncated; the report may contain team or matchup transitions not safely resolved; `AUTO_CANDIDATE` is not a verified record. The parser does not establish the historical public release time. Source remains quarantined from model training.

Next: examine auto manifest and a few original PDF rows, improve parser based on real errors, build independent publication evidence.
