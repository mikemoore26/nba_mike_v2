# S8.22.10.22A — local installed nba_api identity candidates

## Rationale
NBA Stats timed out and the fallback GitHub raw path returned 404. The user's installed `nba_api` 1.11.4 returned 5,103 player records without network access. The local package is a **third-party mutable identity directory**, not an authenticated 2023-24 team roster.

## Method
Capture exact normalized names/IDs from installed package; record version, module path and SHA-256, raw snapshot hash, and source hashes. Reconcile 44 locally corroborated player names, recording unique, ambiguous and absent matches. Team-notice records are excluded. Candidate IDs are not certifications. No manual guesses or source modifications.

## Gates
Fail closed on missing historical source, mismatched hash, broken cardinality, uncorroborated names, malformed/duplicate local registry IDs, or conflicting immutable evidence. No training until historical team membership, injury statuses and as-of timing are independently verified.

## Next milestone
Historical 2023-11-15 roster/team membership corroboration with independently sourced dated evidence, plus alias review for unmatched players.
