"""P0-S4 governed player-game target builder."""
from __future__ import annotations

from typing import Iterable
import pandas as pd

class TargetBuildError(ValueError):
    """Raised when outcome rows violate the target contract."""

IDENTITY = ("game_id", "event_date", "player_id", "team_id")
SOURCE_STATS = ("min", "pts", "reb", "ast", "fg3m")
TARGET_MAP = {
    "min": "target_minutes",
    "pts": "target_points",
    "reb": "target_rebounds",
    "ast": "target_assists",
    "fg3m": "target_3pm",
}

def _require_columns(df: pd.DataFrame, cols: Iterable[str]) -> None:
    missing=[c for c in cols if c not in df.columns]
    if missing:
        raise TargetBuildError(f"missing required columns: {missing}")

def build_player_game_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Build realized player-game outcomes.

    Contract:
    - one row per (game_id, player_id);
    - event_date must parse;
    - identity fields cannot be null;
    - DNP/not-played rows are not fabricated as zero-stat outcomes;
    - zero-minute rows with positive counting stats are impossible;
    - counting targets must be non-negative;
    - target columns are realized outcomes, not predictive features.
    """
    if not isinstance(df, pd.DataFrame):
        raise TargetBuildError("input must be a pandas DataFrame")
    _require_columns(df, (*IDENTITY, *SOURCE_STATS))
    out=df.loc[:, [*IDENTITY, *SOURCE_STATS]].copy()

    if out[list(IDENTITY)].isna().any().any():
        raise TargetBuildError("identity fields cannot be null")
    out["event_date"]=pd.to_datetime(out["event_date"], errors="coerce").dt.date
    if out["event_date"].isna().any():
        raise TargetBuildError("event_date contains invalid values")
    if out.duplicated(["game_id","player_id"]).any():
        raise TargetBuildError("duplicate (game_id, player_id) outcome rows")

    for c in SOURCE_STATS:
        out[c]=pd.to_numeric(out[c], errors="coerce")

    # A row without minutes cannot safely be interpreted as a played game.
    if out["min"].isna().any():
        raise TargetBuildError("minutes missing: DNP/not-played rows must be handled upstream, not converted to zero outcomes")
    if (out["min"] < 0).any():
        raise TargetBuildError("minutes cannot be negative")
    if (out["min"] > 60).any():
        raise TargetBuildError("minutes exceed governed plausibility bound")

    for c in ("pts","reb","ast","fg3m"):
        if out[c].isna().any():
            raise TargetBuildError(f"{c} contains missing realized outcomes")
        if (out[c] < 0).any():
            raise TargetBuildError(f"{c} cannot be negative")

    positive_stats=out[["pts","reb","ast","fg3m"]].sum(axis=1) > 0
    if ((out["min"] == 0) & positive_stats).any():
        raise TargetBuildError("zero-minute row has positive counting statistics")

    out=out.rename(columns=TARGET_MAP)
    out["target_played"]=(out["target_minutes"] > 0).astype("int8")
    ordered=[*IDENTITY,"target_played","target_minutes","target_points","target_rebounds","target_assists","target_3pm"]
    return out.loc[:,ordered].sort_values(["event_date","game_id","player_id"], kind="stable").reset_index(drop=True)
