"""Validation primitives for NBA_MIKE v2."""

from .schema import (
    ColumnRule,
    SchemaContract,
    ValidationIssue,
    ValidationResult,
    validate_records,
)
from .provenance import (
    ProvenanceError,
    assert_parent_manifests_usable,
    validate_parent_chain,
)

__all__ = [
    "ColumnRule",
    "SchemaContract",
    "ValidationIssue",
    "ValidationResult",
    "validate_records",
    "ProvenanceError",
    "assert_parent_manifests_usable",
    "validate_parent_chain",
]

from .invariants import (
    InvariantError,
    assert_d1_boundary,
    assert_entity_history_contract,
    assert_feature_target_separation,
    assert_snapshot_metadata,
    assert_team_opponent_consistency,
    assert_unique_keys,
)

__all__ += [
    "InvariantError",
    "assert_d1_boundary",
    "assert_entity_history_contract",
    "assert_feature_target_separation",
    "assert_snapshot_metadata",
    "assert_team_opponent_consistency",
    "assert_unique_keys",
]
