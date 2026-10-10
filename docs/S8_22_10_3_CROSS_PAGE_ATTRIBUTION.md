# S8.22.10.3 — Cross-page context and slate reconciliation

## Evidence motivating the change

The S8.22.10.2 audit found 41 player candidates, 7 submission notices and 12 ambiguities, including four `n of 4` footer artifacts and eight missing-context events. The archived four-page PDF shows a Toronto player continuing onto page 2, Phoenix players continuing onto page 3, and team-level notices at the top of page 4.

## Design

- Exclude header/footer regions (`y<120`, `y>=525`) based on observed source layout.
- Maintain matchup/team context across pages, reset team on explicit matchup, and reject mismatched team/matchup pairings.
- Record whether candidate context crosses a page boundary.
- Classify each matchup as inside the validated eight-game slate, outside it, or unresolved. Out-of-slate does not mean the official PDF is erroneous.
- Keep player and team submission candidates separate. Preserve original page and y location.
- Fail closed on missing PDF, receipt mismatch, or changed SHA256.

## Limits

The source is a retrospective PDF download, not verified public historical pregame delivery. The parser is source-layout-specific and does not guarantee complete reason wrapping or page-spanning reasons. All outputs remain `MANUAL_REVIEW_REQUIRED`. No model training, bet recommendations or eligibility certification.
