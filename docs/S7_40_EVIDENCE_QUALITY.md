# S7.40 — Evidence Quality and Transaction Direction Review

**Decision:** `RESEARCH_ONLY / BLOCK_TRAINING`.

## Purpose
S7.39's 22 emitted review rows included noisy website chrome, unrelated team names, duplicate statements, and a status-count inconsistency. S7.40 consumes the S7.39 review CSV as-is, without trusting the inconsistent summary counts.

## Controls
- Require S7.39 schema, SHA256-shaped article identifiers, and explicit `false` upstream verification flags.
- Flag statements missing the full player name, with many team mentions, oversized text, page chrome, or no transaction verb.
- Deduplicate identical normalized statements per candidate and article SHA.
- Make **review-only** direction proposals for narrow syntactic patterns such as `TEAM acquired PLAYER from TEAM` and `TEAM traded PLAYER to TEAM`.
- Reject proposals conflicting with tracker destination; detect contradictory proposed directions within a candidate/date.
- Count only emitted output statuses and assert count reconciliation.
- Keep all verification and as-of training flags false; never modify S7.31/S7.26/S7.23.

## Known limits
The direction regex is intentionally incomplete and can miss legitimate articles or encounter long-context ambiguities. Candidate directions must be checked against exact source text, article provenance, player ID, transaction date, and independent evidence. HTML can include navigation and unrelated stories. An article's current retrieval timestamp does not establish historical publication availability.

## Decision gate
S7.40 may produce useful **proposals** for independent review, not accepted historical roster evidence. No training until both independent transaction evidence and historical as-of publication requirements are met.
