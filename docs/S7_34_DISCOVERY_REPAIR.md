# S7.34 — Targeted source discovery and relevance filtering

**Gate:** `RESEARCH_ONLY / BLOCK_TRAINING`.

## Motivation
S7.33 audited 24 captured rows from 2 reused articles; all 24 lacked the corresponding player's full name. S7.34 replaces generic NBA site search with targeted third-party RSS discovery. The third party is a discovery index, **not** an evidentiary source; only official NBA `/news/` pages may be captured.

## Evidence policy
- Search query includes full player name, destination abbreviation, tracker date label and trade context.
- RSS is parsed structurally and candidate article URLs are allowlisted and deduplicated for download.
- Article relevance requires whole player name and transaction language. These can occur far apart and are **leads only**.
- Store search and article bytes under content-addressed SHA-256 objects; emit per-candidate review CSV and report.
- No inferred origin, transaction confirmation, publication-as-of proof, S7.31 evidence promotion or roster intervals.
- Compare `candidate_players_with_relevant_leads` with S7.33's zero, rather than counting successful downloads alone.

## Known limits
Search-engine availability and ranking may vary. Exact player names can miss aliases and accented variants; false negatives are acceptable at this stage. Even relevant articles require independent semantic review and historical publication verification. Live data may include newer articles than the event date.
