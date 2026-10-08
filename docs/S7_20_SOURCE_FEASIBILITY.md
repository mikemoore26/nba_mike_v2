# S7.20 — Historical feasibility and prospective evidence design

## Decision
Five March 2026 official NBA injury PDFs have validated extracted content, but PDF creation metadata and current retrieval cannot establish historical public availability. These PDFs are **not** eligible for as-of model training.

## Source evaluation matrix

| Candidate | What we can establish now | Missing evidence | Decision |
|---|---|---|---|
| Existing official NBA PDF archive | Document content, internal creation metadata, current retrievability | Contemporaneous publicly verifiable capture timestamp per exact version | Research only |
| Independent web archives | Potential historical capture evidence | Exact archived URL, trustworthy archive timestamp, content identity; not yet retrieved/verified | Investigate, not approved |
| Timestamped licensed injury feeds | Potential provider as-of events | Vendor documentation, retention, correction semantics, rights, historical snapshots | Investigate, not approved |
| NBA_MIKE prospective capture | Local UTC retrieval timestamp, exact URL, SHA-256, immutable-by-convention object | Independently authenticated timestamp, server publication time, clock integrity, collection coverage | Prospective evidence only |

## Gates
1. Source content and player/team/matchup fields independently validated.
2. Report version identity retained (URL, hash, raw bytes).
3. Reliable evidence of availability strictly before the prediction cutoff, with timezone conversion and report revisions handled.
4. Injury record eligibility decided per observation, not per source category.
5. No retrospective use of first-seen-today observations for past predictions.

## S7.20 boundaries
Only a manual, exact-URL prospective capture command is implemented. No scheduler, discovery crawler, training pipeline integration, historical timestamp inference, or betting decisions. Do not conflate an internal PDF creation timestamp with public availability.
