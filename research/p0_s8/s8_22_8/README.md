# S8.22.8 — Historical pregame data feasibility

Offline only; no API calls or model training. The manifest is a **blank evidence intake**, not a claim that sources exist. Record only manually reviewed evidence with original bytes archived inside the project and a verified SHA-256. `observed_utc` must mean independently substantiated historical observation/publication time, **not** today's retrieval time. `event_tipoff_utc` is the game-specific cutoff ceiling; production prediction cutoffs may be earlier. `license_status=REVIEWED_PERMITTED` requires a human terms review, not inference.

Run: `python research/p0_s8/s8_22_8/run_s8_22_8.py --project-root . --manifest research/p0_s8/s8_22_8/evidence_manifest.csv`

All categories default to `NOT_ESTABLISHED`. Even if all checks pass, category status is `CANDIDATE_MANUAL_REVIEW_REQUIRED`; training remains blocked. For privacy, do not store API keys or credentials in evidence files. Outputs under `results/` are research artifacts; review before committing. The script does not certify completeness, pregame suitability or rights. Candidate source types: archived injury reports, timestamped lineup announcements, historically captured projections, prior-game play-by-play and box scores with point-in-time joins, archived sportsbook line snapshots. Availability and costs require manual investigation.
