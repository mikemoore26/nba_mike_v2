# S8.22.10.2 — Layout attribution pilot

## Source observations

The archived November 15, 2023 NBA injury PDF has four pages. Text matrix visitor returned stable approximate column x coordinates: matchup 200, team 265, player 425, status 586, reason 666. Delon Wright's reason appears at y=159.3 and y=173.3 around the player/status row y=166.3; Dallas `NOT YET SUBMITTED` is a team-level entry. These observations motivated a coordinate-based, bounded row reconstruction.

## Decision and guardrails

Reconstruct candidate player/status/reason rows and separate team submission candidates. Preserve page and vertical coordinates, fail closed on hash mismatch, flag missing or conflicting team/game context, and avoid silently carrying context between pages. All rows require manual verification against the rendered source. No inference of unlisted-player health, DNP status, or historical availability. No public-as-of certification. `RESEARCH_ONLY / BLOCK_TRAINING`.

## Next review

Run the parser on the original receipt and inspect the candidate CSVs and ambiguities, including page-boundary carryover, wrapped reasons, repeated header rows, team-name variants, and row-count discrepancies. Refine and test before accepting attribution quality.
