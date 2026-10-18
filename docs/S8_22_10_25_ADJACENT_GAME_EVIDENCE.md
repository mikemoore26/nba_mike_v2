# S8.22.10.25 — Adjacent-game historical evidence

## Research question
Can third-party boxscores in the surrounding days provide additional leads for the 35 injury-report candidates not listed on November 15, 2023?

## Method
Acquire ESPN NBA game summaries for November 14, 16, 17 and 18, 2023. Reconcile names against the SHA-256-verified S8.22.10.22A candidate file and S8.22.10.24 report. Preserve raw JSON, retrieval time, URL and digest. Classify same-team, other-team, conflicts, ambiguous ESPN identities, or no listing.

## Interpretation and limits
A player listed on November 14 or 16 is **not thereby proven** to belong to a team on November 15. ESPN IDs are not NBA person IDs; name-only joins may be ambiguous. Boxscore omissions do not prove non-membership. Third-party current retrieval is not an authenticated contemporaneous roster snapshot. Never automatically promote candidates to verified, certified, or training-eligible status.

## Next gates
Acquire dated roster/transaction/inactive evidence; establish ESPN-to-NBA identity mapping; validate publication timestamps; test predictive minutes/usage and market probabilities chronologically; then consider paper ticket simulations before real-money recommendations.
