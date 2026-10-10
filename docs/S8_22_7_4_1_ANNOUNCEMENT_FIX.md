# S8.22.7.4.1 — Announcement-based schedule validation fix

## Problem
The official NBA 2023–24 season schedule announcement names two October 24 opening-night games with matchups and ET tipoff times but omits NBA game IDs. The S8.22.7.4 check for game IDs in announcement bytes would incorrectly reject legitimate evidence.

## Decision
Do not silently weaken the original ID check. Introduce a separate announcement comparison workflow:
1. Verify date-level archived NBA source bytes against the S8.22.7.2 receipt.
2. Require exact visible-text source quotes for matchups, tipoffs, and date coverage.
3. Join manually reviewed rows to S8.22.7.3 official game IDs using independently verified game-page references.
4. Compare team assignments and UTC tipoffs (5-minute tolerance), detect missing/extra games.
5. Return candidate-only status, no date-level or historical-as-of certification.

## Limitations
Quotes are string-presence checks, not full semantic or completeness proofs. A 2026 capture of a page about 2023 does not certify pregame availability. The Oct 24 announcement's 'doubleheader' language is strong date-level evidence but requires human interpretation. Zero-game dates still need a separate negative-evidence protocol. All model and collection gates remain blocked.
