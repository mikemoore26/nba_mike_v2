# S8.22.7.6 — Independent Schedule Evidence Acquisition Queue

**Goal:** Convert the actual five-date S8.22.7.5 audit into an actionable, fail-closed evidence acquisition queue.

**Input:** S8.22.7.5 JSON report, optional user-maintained project-relative receipt manifest. **Outputs:** immutable timestamp/UUID-named JSON and CSV reports with per-date priorities, source-integrity state, and evidence requirements.

**Security/integrity:** no network calls, no `.env` use; reject absolute/traversal paths; validate archived NBA source SHA-256, byte size, official HTTPS hostname, date and timestamp when a receipt is supplied. A valid digest does not prove schedule semantics or no-game evidence.

**Evidence policy:** preserve Oct 24 as candidate control; prioritize Nov 15 and Jan 15 full-date schedule references; require independent negative evidence for June 20; investigate preseason scope for Oct 10, 2026. No automatic approval, no training.
