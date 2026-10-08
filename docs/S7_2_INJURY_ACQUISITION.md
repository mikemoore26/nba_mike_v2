# S7.2 — Official injury PDF acquisition and conservative extraction

Research-only. An exact official NBA injury PDF URL is required; download is opt-in.
Validate URL against S7.1 allowlist; enforce timeout, PDF content type, maximum 12 MB and SHA256. Save immutable-content-named PDF and an audit JSON with download timestamp and filename-derived report timestamp. Extract PDF text by page and status-containing candidate lines for human review. Do not interpret those lines as canonical player-game records.

## Gates still closed
- No independently verified publication/revision timestamp or historical availability proof.
- No stable extraction schema for multi-line player entries, repeated game headers, or 'NOT YET SUBMITTED'.
- No canonical player/team/game IDs or DNP universe.
- No pregame cutoff policy or historical as-of feature authorization.
- No production or betting promotion.

Next: S7.3 schema-aware table extraction and independent timestamp evidence, validated against manually labeled pages.
