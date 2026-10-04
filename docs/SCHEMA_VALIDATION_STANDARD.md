# NBA_MIKE v2 — Schema Validation & Provenance Enforcement Standard

## 1. Purpose

No source artifact becomes trusted canonical input merely because an API request succeeded. NBA_MIKE v2 validates structure, values, uniqueness, and provenance before downstream use.

## 2. Fail-closed rule

Validation failures do not silently coerce, drop, rename, repair, or accept data. Failed or suspicious inputs must be rejected from the trusted path and preserved for investigation/quarantine.

## 3. Contract checks

Dataset contracts may enforce:

- required columns;
- approved data types;
- nullability;
- allowed categorical values;
- numeric lower/upper bounds;
- primary-key uniqueness;
- unexpected-column/schema-drift detection.

Domain limits are explicit contract decisions. They are not universal NBA truths and must be revised deliberately when evidence requires it.

## 4. Schema drift

Unexpected fields, missing fields, or changed types are evidence of source/schema change. Drift must be reviewed rather than silently normalized into an old contract.

## 5. Provenance enforcement

A derived artifact must identify its parent artifacts. A parent used in the trusted path must:

1. have an artifact ID;
2. have validation status `PASS`;
3. have a recorded SHA-256;
4. still match its recorded SHA-256 when the retained bytes are verified.

A quarantined or failed parent cannot be promoted indirectly by deriving a new artifact from it.

## 6. Validation states

The storage standard remains authoritative for lifecycle states:

- `UNVALIDATED`
- `PASS`
- `QUARANTINED`
- `FAILED`

S4's record validator reports `PASS` for a clean contract evaluation and `QUARANTINED` when contract issues exist. Persistent movement/copying into `data/quarantine/` remains a storage workflow responsibility rather than being hidden inside schema validation.

## 7. Separation of responsibilities

Storage/manifests preserve evidence and metadata.

Identity resolves NBA_MIKE entities.

Schema validation determines whether records satisfy an explicit contract.

Provenance enforcement determines whether trusted downstream work may depend on the claimed parent evidence.

These responsibilities must remain separable and testable.

## 8. Modeling gate

S4 is infrastructure. Passing S4 does not authorize model training. The project remains under the current P0 governance and milestone plan.
