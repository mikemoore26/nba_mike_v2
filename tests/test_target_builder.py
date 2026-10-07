import pandas as pd
import pytest
from nba_mike.targets import TargetBuildError, build_player_game_targets

def row(**kw):
    x={"game_id":"G1","event_date":"2025-12-01","player_id":"P1","team_id":"T1",
       "min":32,"pts":21,"reb":7,"ast":5,"fg3m":3}
    x.update(kw); return x

def test_valid_target_build():
    out=build_player_game_targets(pd.DataFrame([row()]))
    assert out.loc[0,"target_points"] == 21
    assert out.loc[0,"target_played"] == 1
    assert "pts" not in out.columns

def test_duplicate_rejected():
    with pytest.raises(TargetBuildError, match="duplicate"):
        build_player_game_targets(pd.DataFrame([row(),row()]))

def test_missing_minutes_not_fabricated_as_zero():
    with pytest.raises(TargetBuildError, match="DNP"):
        build_player_game_targets(pd.DataFrame([row(min=None)]))

def test_negative_stat_rejected():
    with pytest.raises(TargetBuildError, match="cannot be negative"):
        build_player_game_targets(pd.DataFrame([row(ast=-1)]))

def test_impossible_minutes_rejected():
    with pytest.raises(TargetBuildError, match="plausibility"):
        build_player_game_targets(pd.DataFrame([row(min=61)]))

def test_zero_minutes_positive_stats_rejected():
    with pytest.raises(TargetBuildError, match="zero-minute"):
        build_player_game_targets(pd.DataFrame([row(min=0,pts=2,reb=0,ast=0,fg3m=0)]))

def test_zero_minute_zero_stat_row_is_explicit_not_invented():
    out=build_player_game_targets(pd.DataFrame([row(min=0,pts=0,reb=0,ast=0,fg3m=0)]))
    assert out.loc[0,"target_played"] == 0
    assert out.loc[0,"target_points"] == 0

def test_invalid_date_rejected():
    with pytest.raises(TargetBuildError, match="event_date"):
        build_player_game_targets(pd.DataFrame([row(event_date="bad")]))

def test_identity_null_rejected():
    with pytest.raises(TargetBuildError, match="identity"):
        build_player_game_targets(pd.DataFrame([row(player_id=None)]))
