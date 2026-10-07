import numpy as np
import pandas as pd
import pytest
from nba_mike.evaluation.s6_3_diagnostics import validate, diagnostic_report, METHODS

def fixture():
    rows=[]
    for day in range(1,41):
        for player in ('a','b'):
            actual=10. if player=='a' else 25.
            estimate=12. if player=='a' else 20.
            for method,radius in zip(METHODS,(4.,6.,8.)):
                lo=max(0.,estimate-radius);hi=min(60.,estimate+radius)
                rows.append(dict(event_date=f'2026-01-{day:02d}' if day<=31 else f'2026-02-{day-31:02d}',player_id=player,
                    game_id=f'g{day}',method=method,actual=actual,estimate=estimate,lower=lo,upper=hi,
                    covered=int(lo<=actual<=hi),abs_error=abs(actual-estimate),role_change_flag=int(player=='b'),
                    history_group='20+',volatility_group='high' if player=='b' else 'low'))
    return pd.DataFrame(rows)

def test_paired_counts_and_bootstrap_reproducible():
    a=diagnostic_report(fixture(),bootstrap_reps=40,seed=1)
    b=diagnostic_report(fixture(),bootstrap_reps=40,seed=1)
    assert a==b and a['player_games']==80 and a['dates']==40
    assert a['paired_comparisons']['role_history']['width_delta_minutes']>0

def test_missing_method_fails():
    x=fixture().iloc[1:]
    with pytest.raises(ValueError,match='Unpaired'):validate(x)

def test_duplicate_fails():
    x=fixture();x=pd.concat([x,x.iloc[:1]])
    with pytest.raises(ValueError,match='Duplicate'):validate(x)

def test_coverage_inconsistent_fails():
    x=fixture();x.loc[x.index[0],'covered']=1-x.loc[x.index[0],'covered']
    with pytest.raises(ValueError,match='coverage'):validate(x)

def test_cross_method_actual_mismatch_fails():
    x=fixture();i=x.index[x.method=='role_history'][0]
    x.loc[i,'actual']=14.;x.loc[i,'abs_error']=2.;x.loc[i,'covered']=int(x.loc[i,'lower']<=14<=x.loc[i,'upper'])
    with pytest.raises(ValueError,match='Inconsistent actual'):validate(x)

def test_invalid_configuration():
    with pytest.raises(ValueError):diagnostic_report(fixture(),bootstrap_reps=5)
