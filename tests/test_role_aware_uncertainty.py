import pandas as pd
import pytest
from nba_mike.features.role_aware_uncertainty import evaluate_role_calibration, summary

def example():
    return pd.DataFrame([{'event_date': pd.Timestamp('2025-01-01') + pd.Timedelta(days=i),
        'player_id': f'P{j}', 'game_id': f'{i}-{j}', 'actual': 20 + (i % 5) * (j + 1),
        'estimate': 20., 'role_change_flag': j} for i in range(25) for j in (0, 1)])

def run(x):
    return evaluate_role_calibration(x, warmup_dates=6, min_pooled=8, min_group=5)

def test_future_outcome_does_not_change_earlier_intervals():
    x = example()
    a = run(x)
    x.loc[x.event_date == x.event_date.max(), 'actual'] = 60.
    b = run(x)
    columns = ['event_date', 'game_id', 'method', 'radius', 'lower', 'upper']
    pd.testing.assert_frame_equal(a[columns], b[columns])

def test_same_day_groups_do_not_leak():
    x = example()
    a = run(x)
    x.loc[(x.event_date == x.event_date.max()) & (x.role_change_flag == 1), 'actual'] = 60.
    b = run(x)
    assert a[['radius', 'lower', 'upper']].equals(b[['radius', 'lower', 'upper']])

def test_all_methods_same_rows():
    a = run(example())
    assert set(a.method) == {'pooled', 'role_specific', 'shrinkage'}
    assert a.groupby('method').size().nunique() == 1
    assert a.groupby('method').game_id.nunique().nunique() == 1

def test_small_group_falls_back_to_pooled():
    a = evaluate_role_calibration(example(), warmup_dates=6, min_pooled=8, min_group=999)
    radii = a.pivot(index='game_id', columns='method', values='radius')
    assert (radii['pooled'] == radii['role_specific']).all()
    assert (radii['pooled'] == radii['shrinkage']).all()

def test_summary_and_validation():
    a = run(example())
    assert 0 <= summary(a)['coverage'] <= 1
    with pytest.raises(ValueError):
        evaluate_role_calibration(example(), alpha=1)
