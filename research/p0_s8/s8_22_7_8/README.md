# S8.22.7.8 — Team crosswalk and comparison

Offline candidate comparison of the original Nov 15 provider capture and S8.22.7.7 official NBA date report. The included crosswalk is **inferred from the observed matchup rows** and is deliberately labeled `CANDIDATE_INFERRED_FROM_MATCHUPS`. It is **not** independent proof of provider team identities. Verify mappings separately against a saved BALLDONTLIE `/v1/teams` response and its SHA-256 before editing any rows to `VERIFIED_INDEPENDENT`. Even verified metadata is not byte-level receipt validation in this milestone.

Runner validates provider CSV SHA-256 against capture_report.json, date, source statuses, team IDs, matchup uniqueness, official ID uniqueness, UTC tipoffs (5-minute tolerance), missing/extra games, and fails closed. No network, no training. It never marks date completeness or historical as-of certified.
