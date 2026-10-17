# S8.22.10.17 — Player Identity / Injury Evidence Audit

## Purpose
Automate evidence inventory for 44 player candidates from the original 54-row injury ledger without claiming unsupported certifications.

## Controls
- Exact SHA-256 provenance of original ledger and S8.22.10.14 triage.
- Fail closed on duplicate/missing IDs, inconsistent source rows, or unexpected counts.
- Normalize candidate names and flag same-name/same-team collisions.
- Identify missing/odd names, missing literal names in the *already extracted* PDF context, and game-ID mapping issues.
- Exclude 10 team-submission notices from player-injury audit.
- Never infer NBA player IDs or publication timestamps from a candidate name or source excerpt.
- Preserve `RESEARCH_ONLY / BLOCK_TRAINING`.

## Limits and next gate
Local parser excerpts are not independent PDF verification. No player identity, injury status, historical-as-of timing, or training eligibility is certified here. Next acquire authoritative player identifiers and archived, timestamped original injury evidence, with provenance and pregame cutoff controls.
