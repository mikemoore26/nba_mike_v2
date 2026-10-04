from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping
import math


@dataclass(frozen=True)
class ColumnRule:
    name: str
    types: tuple[type, ...]
    nullable: bool = False
    minimum: float | None = None
    maximum: float | None = None
    allowed_values: frozenset[Any] | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ColumnRule.name must be non-empty")
        if not self.types:
            raise ValueError(f"{self.name}: at least one type is required")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError(f"{self.name}: minimum cannot exceed maximum")


@dataclass(frozen=True)
class SchemaContract:
    name: str
    columns: tuple[ColumnRule, ...]
    primary_key: tuple[str, ...] = ()
    allow_extra_columns: bool = False

    def __post_init__(self) -> None:
        names = [c.name for c in self.columns]
        if len(names) != len(set(names)):
            raise ValueError("SchemaContract contains duplicate column rules")
        unknown_keys = set(self.primary_key) - set(names)
        if unknown_keys:
            raise ValueError(f"Primary key columns missing from schema: {sorted(unknown_keys)}")


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    row_index: int | None = None
    column: str | None = None


@dataclass
class ValidationResult:
    contract_name: str
    row_count: int
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.issues

    @property
    def validation_status(self) -> str:
        return "PASS" if self.passed else "QUARANTINED"

    def issue_codes(self) -> list[str]:
        return [issue.code for issue in self.issues]


def _is_null(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float):
        return math.isnan(value)
    return False


def validate_records(
    records: Iterable[Mapping[str, Any]],
    contract: SchemaContract,
) -> ValidationResult:
    rows = [dict(row) for row in records]
    result = ValidationResult(contract_name=contract.name, row_count=len(rows))
    rules = {rule.name: rule for rule in contract.columns}
    required_names = set(rules)

    seen_keys: dict[tuple[Any, ...], int] = {}

    for row_index, row in enumerate(rows):
        present = set(row)
        missing = required_names - present
        for column in sorted(missing):
            result.issues.append(
                ValidationIssue(
                    code="MISSING_COLUMN",
                    message=f"Required column {column!r} is missing",
                    row_index=row_index,
                    column=column,
                )
            )

        if not contract.allow_extra_columns:
            for column in sorted(present - required_names):
                result.issues.append(
                    ValidationIssue(
                        code="SCHEMA_DRIFT_EXTRA_COLUMN",
                        message=f"Unexpected column {column!r}",
                        row_index=row_index,
                        column=column,
                    )
                )

        for column, rule in rules.items():
            if column not in row:
                continue
            value = row[column]

            if _is_null(value):
                if not rule.nullable:
                    result.issues.append(
                        ValidationIssue(
                            code="NULL_NOT_ALLOWED",
                            message=f"{column!r} cannot be null",
                            row_index=row_index,
                            column=column,
                        )
                    )
                continue

            # bool is a subclass of int in Python; reject it unless explicitly allowed.
            type_ok = isinstance(value, rule.types)
            if isinstance(value, bool) and bool not in rule.types:
                type_ok = False
            if not type_ok:
                expected = ", ".join(t.__name__ for t in rule.types)
                result.issues.append(
                    ValidationIssue(
                        code="TYPE_MISMATCH",
                        message=f"{column!r} expected {expected}; got {type(value).__name__}",
                        row_index=row_index,
                        column=column,
                    )
                )
                continue

            if rule.allowed_values is not None and value not in rule.allowed_values:
                result.issues.append(
                    ValidationIssue(
                        code="VALUE_NOT_ALLOWED",
                        message=f"{column!r} has unsupported value {value!r}",
                        row_index=row_index,
                        column=column,
                    )
                )

            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if rule.minimum is not None and value < rule.minimum:
                    result.issues.append(
                        ValidationIssue(
                            code="VALUE_BELOW_MINIMUM",
                            message=f"{column!r}={value!r} is below {rule.minimum}",
                            row_index=row_index,
                            column=column,
                        )
                    )
                if rule.maximum is not None and value > rule.maximum:
                    result.issues.append(
                        ValidationIssue(
                            code="VALUE_ABOVE_MAXIMUM",
                            message=f"{column!r}={value!r} exceeds {rule.maximum}",
                            row_index=row_index,
                            column=column,
                        )
                    )

        if contract.primary_key and all(key in row and not _is_null(row[key]) for key in contract.primary_key):
            key_value = tuple(row[key] for key in contract.primary_key)
            if key_value in seen_keys:
                result.issues.append(
                    ValidationIssue(
                        code="DUPLICATE_PRIMARY_KEY",
                        message=(
                            f"Duplicate primary key {key_value!r}; "
                            f"first seen at row {seen_keys[key_value]}"
                        ),
                        row_index=row_index,
                    )
                )
            else:
                seen_keys[key_value] = row_index

    return result
