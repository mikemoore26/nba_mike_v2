"""S8.8 targeted tests run against installed repository feature builders."""
from pathlib import Path
import importlib.util
import sys

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('s88',ROOT/'research/p0_s8/s8_8/run_s8_8.py')
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def test_real_feature_builders_adversarial():
    results=MOD.execute(ROOT)
    assert len(results)==14,results
    assert all(r['status']=='PASS' for r in results),results

def test_synthetic_fixture_has_two_players_and_same_day_doubleheader():
    x=MOD.sample()
    assert set(x.player_id)=={'A','B'}
    assert len(x.loc[(x.player_id=='A')&(x.event_date=='2025-01-06')])==2

def test_comparison_excludes_only_target_minutes():
    import pandas as pd
    x=pd.DataFrame([{'game_id':'A','player_id':'A','target_minutes':10,'feature':5}])
    y=x.copy();y['target_minutes']=50
    MOD.same(x,y)
    y['feature']=99
    try:MOD.same(x,y)
    except AssertionError:pass
    else:raise AssertionError('feature mutation was not detected')
