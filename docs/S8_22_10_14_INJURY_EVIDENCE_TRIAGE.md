# S8.22.10.14 — Automated injury evidence triage

## Objective
Reduce manual spreadsheet work by systematically auditing the **existing 54 PDF-derived candidate rows** and linking them to the eight independently cross-checked game IDs. Preserve source and review lineage; do not fabricate human certification.

## Verification boundaries
- `AUTOMATED_VERIFIED` for game IDs refers only to prior S8.22.10.13 local evidence integrity and consistency.
- A player name parsed from a PDF is not a verified NBA player identity.
- A status token extracted from a PDF is not an independently certified injury-status observation.
- PDF content hash and local capture receipt **do not establish the publisher's historical release timestamp**.
- A `TEAM_SUBMISSION` notice is not a player injury.
- All 54 records remain `training_eligible=NO`; `BLOCK_TRAINING` is unconditional.

## Outputs
`injury_evidence_triage.csv` (all original records), `exception_queue.csv` (structural/parser/mapping issues), `review.json` (source hashes, counts, decisions). Each candidate retains source page, y coordinate, and PDF context excerpt. Empty exception queue does **not** imply certified player/injury data.

## Next gates
Inspect exception queue; independently establish publisher release time and prediction cutoff; resolve player identities against timestamp-aware roster sources; corroborate row-level injury statuses and team submission semantics. Only then evaluate potential eligibility for future training.
