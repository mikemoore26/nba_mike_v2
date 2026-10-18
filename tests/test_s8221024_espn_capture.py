import importlib.util
from pathlib import Path
import pytest

P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_24/run_s8_22_10_24.py'
spec=importlib.util.spec_from_file_location('s824',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def sample():return {'record_id':'P-001','raw_name':'Wright, Delon','candidate_nba_person_id':'1626153','report_team':'WAS','registry_full_name':'Delon Wright'}
def test_name_normalization():assert m.normalize('  Delón  Wright ')=='delon wright'
def test_reorder():assert 'delon wright' in m.candidate_names(sample())
def test_event_ids():assert m.event_ids({'events':[{'id':'401','date':'2023-11-16T00:00Z'}]})==['401']
def test_no_events():
    with pytest.raises(ValueError):m.event_ids({'events':[]})
def test_duplicate_events():
    with pytest.raises(ValueError):m.event_ids({'events':[{'id':'1'},{'id':'1'}]})
def test_boxscore_entries():
    data={'boxscore':{'players':[{'team':{'abbreviation':'WAS'},'statistics':[{'athletes':[{'athlete':{'id':'10','displayName':'Delon Wright'},'didNotPlay':True}]}]}]}}
    result=m.boxscore_entries(data,'99');assert result[0]['did_not_play'] and result[0]['team']=='WAS'
def test_same_team():
    r=m.reconcile([sample()],[{'name':'Delon Wright','team':'WAS','event_id':'99','espn_athlete_id':'10'}]);assert r[0]['classification']=='SAME_TEAM_BOX_SCORE_LISTING_UNCERTIFIED';assert r[0]['historical_team_verified']=='NO'
def test_other_team():
    r=m.reconcile([sample()],[{'name':'Delon Wright','team':'BOS','event_id':'99','espn_athlete_id':'10'}]);assert r[0]['classification']=='OTHER_TEAM_BOX_SCORE_LISTING_REVIEW'
def test_missing_not_negative():assert m.reconcile([sample()],[])[0]['classification']=='NO_BOX_SCORE_LISTING_NOT_NEGATIVE_PROOF'
def test_conflict():
    entries=[{'name':'Delon Wright','team':t,'event_id':str(i),'espn_athlete_id':'10'} for i,t in enumerate(('WAS','BOS'))]
    assert m.reconcile([sample()],entries)[0]['classification']=='CONFLICTING_GAME_DAY_BOX_SCORE_LISTINGS'
def test_immutable(tmp_path):
    p=tmp_path/'a';m.immutable(p,b'abc');m.immutable(p,b'abc')
    with pytest.raises(ValueError):m.immutable(p,b'def')
def test_csv_schema():assert m.csv_blob(m.reconcile([sample()],[])).decode().splitlines()[0].startswith('record_id,raw_name')
