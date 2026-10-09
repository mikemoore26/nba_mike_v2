# S8.19 — Publication evidence audit

Scope: 2023-10-24 LAL@DEN, game `0022300061`, scheduled 19:30 America/New_York. Priority sources: Denver Nuggets October 23 team preview and NBA 6 PM injury-report PDF from S8.18.

The runner checks actual bytes against the S8.18 SHA256 manifest, extracts HTML publication meta tags and embedded PDF creation/modification date claims, and classifies manually submitted archive capture candidates against tipoff. All claims are unverified. The intake has no mechanism to independently validate archive authority, historical capture time, replay integrity or public accessibility. It therefore **never** marks an artifact or game verified.

Source independence caveats: NBA and Denver Nuggets are affiliated; editorial metadata may be backfilled; contemporary downloads cannot establish historical publication. Neither article nor injury report constitutes complete pregame roster eligibility or DNP reconciliation. The 88 restart-period games are outside this pilot and remain blocked.

Decision: `RESEARCH_ONLY / BLOCK_TRAINING`. Next action: inspect report; if no independently authenticated archival replay exists, record this source as historical publication unverified and pivot to a different data provenance strategy rather than repeatedly querying the same failing endpoint.
