import csv
import importlib.util
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_5/run_s8_22_5.py'
spec=importlib.util.spec_from_file_location('s8225',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def write(path, fields, data):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(data)
def provider(tmp_path,records):
    p=tmp_path/'provider.csv';write(p,m.FIELDS,records);return p
def record(**kw):
    return dict(provider='balldontlie',provider_game_id='10',official_nba_game_id='',game_date='2023-10-24',home_provider_team_id='1',away_provider_team_id='2',tipoff_utc='2023-10-24T23:30:00+00:00',tipoff_status='PRESENT_UNVERIFIED',game_status='Final',**kw)
def refs(tmp_path,tip='2023-10-24T23:30:00Z'):
    o=tmp_path/'official.csv';t=tmp_path/'teams.csv'
    write(o,['official_nba_game_id','game_date','home_team','away_team','tipoff_utc'],[dict(official_nba_game_id='0022300061',game_date='2023-10-24',home_team='DEN',away_team='LAL',tipoff_utc=tip)])
    write(t,['provider_team_id','official_team'],[dict(provider_team_id='1',official_team='DEN'),dict(provider_team_id='2',official_team='LAL')]);return o,t
def test_empty_unverified(tmp_path):
    r,c=m.audit(provider(tmp_path,[]),'2026-10-10');assert r['schedule_state']=='EMPTY_SCHEDULE_UNVERIFIED' and not c
def test_empty_contradicted(tmp_path):
    o,t=refs(tmp_path);r,_=m.audit(provider(tmp_path,[]),'2023-10-24',o,t,'manual example')
    assert r['schedule_state']=='EMPTY_SCHEDULE_CONTRADICTED_BY_REFERENCE'
def test_candidate_not_certified(tmp_path):
    o,t=refs(tmp_path);r,c=m.audit(provider(tmp_path,[record()]),'2023-10-24',o,t,'manual example')
    assert r['schedule_state']=='CANDIDATE_DATE_COVERAGE_MATCH_REQUIRES_REVIEW'
    assert r['decision']=='BLOCK_TRAINING' and c[0]['match_status']=='MATCH_TIME_WITHIN_5_MIN'
def test_tipoff_mismatch(tmp_path):
    o,t=refs(tmp_path,'2023-10-24T22:00:00Z');r,c=m.audit(provider(tmp_path,[record()]),'2023-10-24',o,t,'manual example')
    assert c[0]['match_status']=='TIME_DISAGREES' and r['tipoff_accuracy']=='UNVERIFIED'
def test_missing_source(tmp_path):
    o,t=refs(tmp_path)
    with pytest.raises(ValueError,match='PROVENANCE'):m.audit(provider(tmp_path,[]),'2023-10-24',o,t)
def test_partial_input(tmp_path):
    o,t=refs(tmp_path)
    with pytest.raises(ValueError,match='TOGETHER'):m.audit(provider(tmp_path,[]),'2023-10-24',o)
def test_missing_columns(tmp_path):
    p=tmp_path/'x.csv';p.write_text('foo\nbar\n')
    with pytest.raises(ValueError,match='MISSING_COLUMNS'):m.audit(p,'2023-10-24')
def test_other_dates(tmp_path):
    r,c=m.audit(provider(tmp_path,[record()]),'2026-10-10');assert r['other_date_rows']==1 and r['provider_rows']==0
def test_invalid_date(tmp_path):
    with pytest.raises(ValueError):m.audit(provider(tmp_path,[]),'2026/10/10')
def test_invalid_team_map(tmp_path):
    o,t=refs(tmp_path);withheld=[{'provider_team_id':'1','official_team':'DEN'},{'provider_team_id':'1','official_team':'DEN'}]
    write(t,['provider_team_id','official_team'],withheld)
    with pytest.raises(ValueError,match='INVALID_TEAM_CROSSWALK'):m.audit(provider(tmp_path,[record()]),'2023-10-24',o,t,'manual example')
def test_no_time_claim(tmp_path):
    assert m.utc('2023-10-24') is None
