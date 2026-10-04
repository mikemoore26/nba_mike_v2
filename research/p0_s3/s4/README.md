# P0-S3 S4 — Schema Validation & Provenance Enforcement

## Goal

Prevent malformed, drifted, duplicated, impossible, unverified, or quarantined data from silently entering canonical NBA_MIKE v2 datasets.

## Acceptance

Run from the project root:

```powershell
python -m pytest ".\tests\test_schema_validation.py" -q
python ".\research\p0_s3\s4\run_s4_acceptance.py"
```

S4 passes only when every acceptance check passes.

## Design rule

Validation is fail-closed. A failed artifact is evidence to preserve and investigate, not a reason to weaken a contract merely to keep the pipeline moving.

S4 does not train predictive models.
