# S8.22.7.9 — Independent team-directory verification

The November 15, 2023 S8.22.7.8 comparison matched eight games, but its 16 team-ID mappings were inferred from matchups, not independently sourced. This milestone adds an offline verifier for **archived BALLDONTLIE `/v1/teams` directory JSON bytes**. It validates the original file's SHA-256/length, official URL, directory IDs and abbreviations, missing/duplicate/conflicting IDs, and the candidate comparison's referenced team abbreviations. The tool does not fetch or authorize data collection.

A user-managed, manual capture is required unless the project already has a genuine archived team-directory response. A supplied CSV alone is insufficient. The receipt maker does not certify the user's retrieval time; the user must enter the actual UTC timestamp. Archived retrospective team identity evidence does not certify historical pregame availability or date completeness.

Decision remains `RESEARCH_ONLY / BLOCK_TRAINING` regardless of a directory match. No model training, no automated provider collection, no schedule-completeness approval.
