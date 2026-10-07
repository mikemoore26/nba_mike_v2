import pandas as pd
import pytest
from nba_mike.features.conditional_uncertainty import evaluate_conditional,summary

def sample():
    return pd.DataFrame([{'event_date':f'2025-01-{i+1:02d}','player_id':'P',
        'game_id':f'G{i}','actual':20+i%4,'estimate':20.,'prior_dates':i,
        'role_change_flag':int(i%5==0)} for i in range(25)])

def test_no_future_outcome_leak():
    a=sample();p=evaluate_conditional(a,warmup_dates=7,min_pooled=2,min_group=2,min_cell=2)
    a.loc[24,'actual']=50
    q=evaluate_conditional(a,warmup_dates=7,min_pooled=2,min_group=2,min_cell=2)
    pd.testing.assert_frame_equal(p.iloc[:-3].reset_index(drop=True),q.iloc[:-3].reset_index(drop=True))

def test_same_day_calibration_frozen():
    a=sample();r=a.iloc[-1].copy();r['player_id']='Q';r['game_id']='Q1';r['actual']=55
    a=pd.concat([a,pd.DataFrame([r])],ignore_index=True)
    p=evaluate_conditional(a,warmup_dates=7,min_pooled=2,min_group=2,min_cell=2)
    last=p[p.event_date==pd.Timestamp('2025-01-25')]
    assert len(last)==6
    assert last.groupby('method').radius.nunique().max()==1

def test_methods_and_summary():
    p=evaluate_conditional(sample(),warmup_dates=7,min_pooled=2,min_group=2,min_cell=2)
    assert set(p.method)=={'role_specific','role_history','role_history_volatility'}
    assert 0<=summary(p)['coverage']<=1

def test_bad_inputs():
    with pytest.raises(ValueError):evaluate_conditional(sample(),alpha=0)
    with pytest.raises(ValueError):evaluate_conditional(sample().drop(columns=['prior_dates']))

def test_history_groups():
    p=evaluate_conditional(sample(),warmup_dates=7,min_pooled=2,min_group=2,min_cell=2)
    assert {'5-9','10-19','20+'}==set(p.history_group)
