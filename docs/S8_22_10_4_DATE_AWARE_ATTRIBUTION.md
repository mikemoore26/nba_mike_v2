# S8.22.10.4 — Date-aware attribution and scope reconciliation

- Input: archived original NBA injury report PDF from S8.22.10 with SHA-256 receipt verification.
- Fix: include y=90.9 and y=114.0 page-four table entries (previous y>=120 filter discarded both); preserve game date across pages and reset game/team on an explicit date change.
- Distinguish report edition timestamp from each listed game date; scope is `(game_date == 2023-11-15) AND (matchup in validated eight-game slate)`.
- Regression coverage: Lakers SAC@LAL 11/15; Nets and Heat BKN@MIA 11/16; Thunder and Warriors OKC@GSW 11/16; date-scoped membership; cross-page continuation; title/footer exclusion.
- Outputs: player and team submission candidates, ambiguity ledger, out-of-slate candidates, JSON summary.
- Risks: coordinate heuristic; multi-line reason association; team names; slate completeness; player identity; as-of public accessibility remain unverified. Manual original-PDF row verification required.
- Governance: `RESEARCH_ONLY / BLOCK_TRAINING`. Never promote candidate extraction to historical availability, DNP, or model-training evidence without independent gates.
