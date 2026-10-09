# S8.2 — Schema recognition repair

S8.1 scanned 75,445 rows across three snapshots, but falsely reported MISSING_DATE_COLUMN and NO_STAT_TARGET_COLUMNS because `event_date` and lowercase `pts`, `reb`, `ast`, `fg3m` were omitted from recognition logic.

S8.2 is a separate read-only runner. It accepts `event_date` and `EVENT_DATE`, matches stat targets case-insensitively, checks nonfinite numeric targets, and reruns existing row-level duplicate/date/minutes/negative-value tests. The S8.1 code and source snapshots are not overwritten.

Do not interpret quality success as pre-tipoff feature availability. All training, historical roster/transaction feature usage, deployment and betting promotion remain blocked.

Next: inspect S8.2 report for genuine row-level defects; then verify lagged feature construction and chronological OOS before proposing any research baseline.
