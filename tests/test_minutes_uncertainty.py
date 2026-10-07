import pandas as pd
import pytest
from nba_mike.features.minutes_uncertainty import uncertainty_frame,summarize

def sample():
    return pd.DataFrame([{"event_date":f"2025-01-{i+1:02d}","player_id":"P",
       "game_id":f"G{i}","target_minutes":20.+i%4,"ewm_5":20.,
       "prior_dates":i,"role_change_flag":0} for i in range(20)])
def test_no_future_error_changes_past_intervals():
    x=sample()
    a=uncertainty_frame(x,warmup_dates=7,min_calibration=2)
    x.loc[19,"target_minutes"]=50.
    b=uncertainty_frame(x,warmup_dates=7,min_calibration=2)
    pd.testing.assert_frame_equal(a.iloc[:-1].reset_index(drop=True),b.iloc[:-1].reset_index(drop=True))
def test_same_day_outcomes_cannot_calibrate_each_other():
    x=sample()
    extra=x.iloc[-1].copy();extra["player_id"]="Q";extra["game_id"]="Q1";extra["target_minutes"]=55.
    x=pd.concat([x,pd.DataFrame([extra])],ignore_index=True)
    y=uncertainty_frame(x,warmup_dates=7,min_calibration=2)
    last=y[y.event_date==pd.Timestamp("2025-01-20")]
    assert len(last)==2
    assert last.radius.nunique()==1
    assert last.calibration_n.nunique()==1
def test_invalid_alpha():
    with pytest.raises(ValueError):uncertainty_frame(sample(),alpha=1)
def test_summary():
    x=uncertainty_frame(sample(),warmup_dates=7,min_calibration=2)
    assert 0<=summarize(x)["coverage"]<=1
def test_early_dates_not_predicted():
    x=uncertainty_frame(sample(),warmup_dates=7,min_calibration=2)
    assert x.event_date.min()>=pd.Timestamp("2025-01-08")
