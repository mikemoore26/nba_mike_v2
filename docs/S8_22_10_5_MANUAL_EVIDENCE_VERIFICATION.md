# S8.22.10.5 — Evidence verification review packet

## Objective
Prepare all S8.22.10.4 player and team submission candidates for **human, source-anchored verification**, without declaring them verified. Preserve SHA-256-checked original PDF provenance and existing extraction output.

## Inputs
- Archived four-page November 15, 2023 injury report PDF, SHA-256 `18b5baaaccaf7b9e96529e40191432cd5ec2fc42ab3ca363e7d77d2a78c8873a`.
- S8.22.10.4 result `review.json`, `player_status_candidates.csv`, `team_submission_candidates.csv`.
- Prior recorded eight-game slate: DAL@WAS, ATL@NYK, PHI@BOS, TOR@MIL, CHI@ORL, PHX@MIN, LAL@SAC, POR@CLE.

## Known issues
- S8.22.10.4 retains a page-1 column-header ambiguity `Player Name / Current Status` (y=115.2). The review packet flags header-shaped rows if they occur among candidate records; the underlying parser is not modified.
- Some prior slate home/away orientations disagree with the PDF, including MIN@PHX versus PHX@MIN. These are not automatically resolved.
- The PDF contains Nov 16 entries; report edition date and game date must not be conflated.

## Outputs and decision gate
Every row remains `PENDING` until an accountable reviewer checks the PDF visually. The review packet does not certify publication timestamp, historical as-of access, player identity, DNP eligibility, completeness, or modeling suitability. `BLOCK_TRAINING` persists.
