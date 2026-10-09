"""S8.10 standalone fail-closed predictor and chronological split contract.

RESEARCH_ONLY. Not wired into model training. No as-of/eligibility certification.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd


class ContractViolation(ValueError):
    pass


# Identifiers are never model predictors in this contract. Exact, normalized
# outcome aliases and common derived labels are forbidden as well.
FORBIDDEN_EXACT = frozenset({
    'min', 'minutes', 'pts', 'points', 'reb', 'rebounds', 'ast', 'assists',
    'fg3m', '3pm', 'threes', 'target_minutes', 'target_points',
    'target_rebounds', 'target_assists', 'target_3pm', 'game_id',
    'player_id', 'team_id', 'event_date', 'game_date', 'date',
    'actual_minutes', 'actual_points', 'actual_rebounds',
    'actual_assists', 'actual_3pm', 'realized_minutes',
    'realized_points', 'realized_rebounds', 'realized_assists',
    'realized_3pm', 'label', 'outcome', 'y', 'target',
})


def normalize(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ContractViolation('column names must be nonempty strings')
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')


def _reject_name(name: str) -> None:
    n = normalize(name)
    if (n in FORBIDDEN_EXACT or n.startswith(('target_', 'actual_', 'realized_', 'label_', 'outcome_'))
            or n.endswith(('_target', '_actual', '_realized', '_label', '_outcome'))):
        raise ContractViolation(f'forbidden predictor column: {name}')


def validate_predictors(frame: pd.DataFrame, allowed: Sequence[str]) -> pd.DataFrame:
    """Return numeric-only X with exactly approved columns; never auto-select.

    Extra source columns are not included. The caller must separately establish
    that *each approved feature* is genuinely pregame and as-of available.
    """
    if not isinstance(frame, pd.DataFrame):
        raise ContractViolation('frame must be a DataFrame')
    if not isinstance(allowed, (list, tuple)) or not allowed:
        raise ContractViolation('explicit nonempty list/tuple of approved predictors required')
    if not frame.columns.is_unique:
        raise ContractViolation('duplicate source columns')
    if len(set(allowed)) != len(allowed):
        raise ContractViolation('duplicate approved predictors')
    if len({normalize(x) for x in allowed}) != len(allowed):
        raise ContractViolation('normalized predictor name collision')
    for name in allowed:
        _reject_name(name)
        if name not in frame.columns:
            raise ContractViolation(f'missing approved predictor: {name}')
    x = frame.loc[:, list(allowed)].copy()
    for name in x.columns:
        if not pd.api.types.is_numeric_dtype(x[name]) or pd.api.types.is_bool_dtype(x[name]):
            raise ContractViolation(f'non-numeric predictor: {name}')
    try:
        finite = np.isfinite(x.to_numpy(dtype=float))
    except (ValueError, TypeError, OverflowError) as exc:
        raise ContractViolation('predictor cannot be represented as finite float') from exc
    if not finite.all():
        raise ContractViolation('missing or non-finite predictor value')
    return x


@dataclass(frozen=True)
class FoldBoundaries:
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


def validate_chronological_fold(train_dates: Sequence, test_dates: Sequence) -> FoldBoundaries:
    """Require nonempty, strictly date-separated folds; no same-day train/test.

    Date separation alone does NOT prove fold-local fitting or data provenance.
    """
    train = pd.to_datetime(pd.Series(train_dates), errors='coerce', utc=True)
    test = pd.to_datetime(pd.Series(test_dates), errors='coerce', utc=True)
    if train.empty or test.empty or train.isna().any() or test.isna().any():
        raise ContractViolation('fold dates must be nonempty and valid')
    train_day = train.dt.normalize()
    test_day = test.dt.normalize()
    if train_day.max() >= test_day.min():
        raise ContractViolation('train/test overlap or same-day boundary')
    return FoldBoundaries(train_day.max(), test_day.min(), test_day.max())


def assert_research_only() -> None:
    """No training permission is granted by S8.10."""
    raise ContractViolation('BLOCK_TRAINING: historical as-of and player eligibility unverified')
