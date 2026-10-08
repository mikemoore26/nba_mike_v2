"""S7.0: timestamp-aware, fail-closed audit of proposed pregame observations."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Mapping

REQUIRED = ('source_id', 'game_id', 'player_id', 'field', 'value',
            'observed_at_utc', 'available_at_utc', 'prediction_cutoff_utc')


def _utc(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError('timestamp must be a nonempty ISO-8601 string with UTC offset')
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('invalid ISO-8601 timestamp') from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError('naive timestamp forbidden')
    return dt.astimezone(timezone.utc)


def audit_observation(record: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed: availability must be known by cutoff, not merely observed earlier."""
    missing = [k for k in REQUIRED if k not in record or record[k] is None or record[k] == '']
    if missing:
        return {'eligible': False, 'reason': 'missing_required:' + ','.join(missing)}
    try:
        observed = _utc(record['observed_at_utc'])
        available = _utc(record['available_at_utc'])
        cutoff = _utc(record['prediction_cutoff_utc'])
    except ValueError as exc:
        return {'eligible': False, 'reason': 'invalid_timestamp:' + str(exc)}
    if available < observed:
        return {'eligible': False, 'reason': 'availability_before_observation'}
    if observed > cutoff:
        return {'eligible': False, 'reason': 'observed_after_cutoff'}
    if available > cutoff:
        return {'eligible': False, 'reason': 'available_after_cutoff'}
    if record.get('is_revised') is True and not record.get('revision_asof_verified'):
        return {'eligible': False, 'reason': 'revision_asof_unverified'}
    return {'eligible': True, 'reason': 'eligible_at_cutoff'}


def summarize_records(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for record in records:
        result = audit_observation(record)
        counts[result['reason']] = counts.get(result['reason'], 0) + 1
    return {'total': len(records), 'eligible': counts.get('eligible_at_cutoff', 0),
            'reasons': dict(sorted(counts.items()))}
