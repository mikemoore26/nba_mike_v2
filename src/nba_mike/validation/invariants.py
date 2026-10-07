from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable, Mapping, Sequence


class InvariantError(ValueError):
    """Raised when a governed NBA_MIKE data invariant is violated."""


def _date(value: Any, field: str) -> date:
    try:
        return date.fromisoformat(str(value)[:10])
    except Exception as exc:
        raise InvariantError(f"INVALID_DATE: field={field} value={value!r}") from exc


def assert_d1_boundary(rows: Iterable[Mapping[str, Any]], *, target_game_date: str,
                       date_field: str = "event_date") -> None:
    target = _date(target_game_date, "target_game_date")
    cutoff = target.fromordinal(target.toordinal() - 1)
    for i, row in enumerate(rows):
        event = _date(row.get(date_field), date_field)
        if event > cutoff:
            raise InvariantError(
                f"D1_LEAKAGE: row={i} {date_field}={event.isoformat()} cutoff={cutoff.isoformat()}"
            )


def assert_unique_keys(rows: Iterable[Mapping[str, Any]], *,
                       key_fields: Sequence[str] = ("game_id", "player_id")) -> None:
    seen: set[tuple[str, ...]] = set()
    for i, row in enumerate(rows):
        key = tuple(str(row.get(k, "")).strip() for k in key_fields)
        if any(not value for value in key):
            raise InvariantError(f"MISSING_KEY: row={i} fields={tuple(key_fields)}")
        if key in seen:
            raise InvariantError(f"DUPLICATE_KEY: row={i} key={key}")
        seen.add(key)


def assert_team_opponent_consistency(rows: Iterable[Mapping[str, Any]], *,
                                     team_field: str = "team_id",
                                     opponent_field: str = "opponent_team_id") -> None:
    for i, row in enumerate(rows):
        team = str(row.get(team_field, "")).strip()
        opponent = str(row.get(opponent_field, "")).strip()
        if not team or not opponent:
            raise InvariantError(f"TEAM_OPPONENT_MISSING: row={i}")
        if team == opponent:
            raise InvariantError(f"TEAM_EQUALS_OPPONENT: row={i} team_id={team}")


def assert_feature_target_separation(feature_rows: Iterable[Mapping[str, Any]], *,
                                     forbidden_target_fields: Iterable[str]) -> None:
    forbidden = {str(x).strip() for x in forbidden_target_fields if str(x).strip()}
    if not forbidden:
        raise InvariantError("TARGET_FIELD_CONTRACT_EMPTY")
    for i, row in enumerate(feature_rows):
        overlap = sorted(forbidden.intersection(row.keys()))
        if overlap:
            raise InvariantError(f"TARGET_LEAKAGE: row={i} forbidden_fields={overlap}")


def assert_snapshot_metadata(metadata: Mapping[str, Any], *, target_game_date: str) -> None:
    target = _date(target_game_date, "target_game_date")
    cutoff = target.fromordinal(target.toordinal() - 1)
    if metadata.get("contract") != "D-1":
        raise InvariantError("SNAPSHOT_CONTRACT_NOT_D1")
    if str(metadata.get("target_game_date", "")) != target.isoformat():
        raise InvariantError("SNAPSHOT_TARGET_DATE_MISMATCH")
    if str(metadata.get("cutoff_date", "")) != cutoff.isoformat():
        raise InvariantError("SNAPSHOT_CUTOFF_MISMATCH")
    as_of = str(metadata.get("as_of_time", ""))
    try:
        parsed = datetime.fromisoformat(as_of)
    except Exception as exc:
        raise InvariantError("SNAPSHOT_AS_OF_INVALID") from exc
    if parsed.date() != cutoff:
        raise InvariantError("SNAPSHOT_AS_OF_DATE_MISMATCH")
    for field in ("parent_artifact_id", "parent_sha256", "logical_sha256", "snapshot_id"):
        if not str(metadata.get(field, "")).strip():
            raise InvariantError(f"SNAPSHOT_PROVENANCE_MISSING: {field}")


def assert_entity_history_contract(metadata: Mapping[str, Any]) -> None:
    for i, item in enumerate(metadata.get("entity_history", [])):
        count = item.get("eligible_game_count")
        status = item.get("history_status")
        if not isinstance(count, int) or count < 0:
            raise InvariantError(f"ENTITY_HISTORY_COUNT_INVALID: row={i}")
        expected = "AVAILABLE" if count else "ZERO_HISTORY"
        if status != expected:
            raise InvariantError(
                f"ENTITY_HISTORY_STATUS_INVALID: row={i} count={count} status={status!r}"
            )
