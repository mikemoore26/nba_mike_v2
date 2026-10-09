# S8.1 — Player game-log quality audit

## Goal
Direct row-level audit of the three S8.0-discovered player game-log snapshots. No inference of provenance from filenames or column names.

## Checks
- File presence, SHA-256, headers, record counts, date range, broad season window, player/game identifiers, duplicate player-game keys.
- Minutes parseability (`MM:SS` and numeric), plausible 0–75-minute range.
- Missing, nonnumeric, negative and extreme numeric target statistics.
- Cross-season schema inventory and gaps.
- Scan cap and read errors are explicit blockers, not silent successes.

## Interpretation
Even when quality checks pass, **postgame statistics are outcomes**, not features available before tipoff. Historical publication, team membership, injury information, DNP coverage, schedule completeness, chronological OOS execution, and historical market availability remain unverified. No training or betting promotion is authorized. S7.51 roster/transaction restrictions remain active.
