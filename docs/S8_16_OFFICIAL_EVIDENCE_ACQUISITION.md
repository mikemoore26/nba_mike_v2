# S8.16 — Official artifact acquisition and timestamp evidence

Scope: LAL@DEN, October 24 2023, game 0022300061, scheduled 7:30 PM ET; NBA 5 PM injury-report candidate.

The runner attempts bounded HTTPS retrieval **only on explicit opt-in** from the official NBA static host and the Internet Archive CDX index. It saves original response bytes, SHA-256, size, and a machine-readable inventory. It inspects PDF signature and embedded date *claims*. It classifies CDX timestamps relative to scheduled tipoff as `CANDIDATE_PRE_TIPOFF_CAPTURE`, `POST_TIPOFF`, or `REJECTED`.

**All evidence remains `UNVERIFIED`**: an index entry alone does not prove that the same document bytes were publicly available at the indexed time. Independent review must compare archived replay content with the official source, corroborate the capture timestamp with archive provenance, inspect any redirect/rewriting, and establish source identity. Even then, a single injury report is not a complete pregame player universe. No live training integration or model fitting.

Do not infer historical publication from PDF `CreationDate`, HTTP `Last-Modified`, printed time, or today's download timestamp. Do not approve the 88 unresolved restart-period games. Any failures or unavailable sources must remain unresolved and be documented.
