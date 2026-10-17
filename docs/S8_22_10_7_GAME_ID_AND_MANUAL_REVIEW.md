# S8.22.10.7 — Provisional Game-ID Crosswalk and Evidence Review

**Scope:** Stage a corrected away@home crosswalk and a 54-row manual evidence review ledger without mutating prior milestones.

**Sources:** S8.22.10.6 unique matchup reconciliation and S8.22.10.5 original manual review ledger. Earlier NBA game-ID associations are treated as **provisional, not certified**.

**Gates:** Source input hashes, unique keys, eight target games present, independent orientation status corroborated, record-count parity, unique review IDs. Fail closed on any mismatch.

**Outputs:** provisional_game_id_crosswalk.csv, player_and_team_manual_review.csv, review.json.

**Limitations:** No official game-ID verification in this patch; all 54 manual decisions pending. No publication-time certification, player identity certification, eligibility/DNP evidence, or training permission.

**Governance:** `RESEARCH_ONLY / BLOCK_TRAINING`.
