# S8.22.10.29 — Controlled Smoke Plan

Source review: canonical builder, snapshot builder, identity registry, schema, leakage invariants, provenance, opportunity and adaptive-form modules; plus five associated tests.

## Findings before runtime

- Canonical builder verifies parent provenance and resolves player/team IDs; existing tests include happy path, quarantined parent and tampering checks.
- Snapshot builder verifies parent SHA and builds D-1 rows; its direct tests were **not included** in the upload.
- Schema tests cover missing fields, type mismatch, invalid ranges and duplicate keys.
- Leakage tests cover D-1 cutoff, duplicate keys, team/opponent consistency and forbidden target fields.
- Opportunity tests cover prior-only shifted features, cold start and invalid inputs.
- Adaptive-form tests cover same-date history, future mutation and prequential behavior.
- Predictions and market/ticket contracts remain unselected and unverified.

## Scope

Run only the five known test modules through a gated subprocess. Record pass/fail per module. No network data collection, model fitting, odds requests, or ticket creation. A passing suite is evidence of local unit-test compatibility, not production readiness.

## Next decision

Review failures and source contracts; inspect snapshot-specific tests and then build synthetic **cross-module** fixtures only after the isolated tests pass. Do not upgrade historical data, OOS, market or ticket gates from this milestone.
