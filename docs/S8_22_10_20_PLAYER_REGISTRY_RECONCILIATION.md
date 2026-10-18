# S8.22.10.20 — Player Identity Registry Reconciliation

## Goal

Turn the 44 locally corroborated names from S8.22.10.19 into a reproducible identity-candidate queue, without assuming that PDF name matching establishes an NBA player ID.

## Method

1. Verify the source ledger and S8.22.10.18 diagnostic by SHA-256.
2. Verify the S8.22.10.19 report links to the same evidence and reports 44 local matches.
3. Parse an optional raw official NBA Stats `CommonAllPlayers` JSON response; no API calls are performed.
4. Match exact normalized full names. Require a unique player ID and matching team to propose an ID. Any mismatch or ambiguity remains in the exception class.
5. Record source hashes, candidate classes, and a fail-closed decision.

## Caveats

The historical team must be independently validated for the target date; NBA roster registries can reflect different seasons or current affiliations. The script cannot verify an input JSON's authenticity or season from its schema. A proposed ID is **not certified**. No injury statuses or historical publication times are certified. No original evidence is modified. An inventory run without a registry is useful and expected to produce 44 `REGISTRY_NOT_SUPPLIED` rows.

**Governance: `RESEARCH_ONLY / BLOCK_TRAINING`.**
