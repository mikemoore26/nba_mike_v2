import csv,importlib.util
from pathlib import Path
import pytest
MOD=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_7/run_s8_22_7.py'
spec=importlib.util.spec_from_file_location('s8227',MOD);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def write(path,fields,rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 return path

@pytest.fixture
def inputs(tmp_path):
 p=write(tmp_path/'p.csv',sorted(m.PROVIDER_COLUMNS),[dict(provider_game_id='1',game_date='2023-10-24',home_provider_team_id='8',away_provider_team_id='14',tipoff_utc='2023-10-24T23:30:00Z')]);
 r=write(tmp_path/'r.csv',sorted(m.REFERENCE_COLUMNS),[dict(game_date='2023-10-24',official_nba_game_id='0022300061',home_team='DEN',away_team='LAL',tipoff_utc='2023-10-24T23:30:00Z',source_url='https://nba.com/game/one',evidence_sha256='a'*64,evidence_retrieved_utc='2026-10-09T20:00:00Z')]);return p,r

def test_match_candidate(inputs):
 p,r=inputs;out=m.audit_date('2023-10-24',p,r,{'8':'DEN','14':'LAL'});assert out['status']=='CANDIDATE_MATCH_REVIEW_REQUIRED';assert out['matched_candidates']==1

def test_missing_provider(inputs):assert m.audit_date('2023-10-24',None,inputs[1],{})['status']=='PROVIDER_SNAPSHOT_MISSING'
def test_missing_reference(inputs):assert m.audit_date('2023-10-24',inputs[0],None,{})['status']=='INDEPENDENT_REFERENCE_MISSING'
def test_wrong_date(inputs):assert m.audit_date('2023-10-25',*inputs,{})['status']=='PROVIDER_DATE_MISMATCH'
def test_unmapped(inputs):assert m.audit_date('2023-10-24',*inputs,{})['status']=='COVERAGE_MISMATCH'
def test_tipoff(inputs):
 p,r=inputs;rows=m.read_csv(p,m.PROVIDER_COLUMNS);rows[0]['tipoff_utc']='2023-10-24T23:45:00Z';write(p,sorted(m.PROVIDER_COLUMNS),rows)
 assert m.audit_date('2023-10-24',p,r,{'8':'DEN','14':'LAL'})['status']=='TIPOFF_DISCREPANCY'
def test_duplicate_provider(inputs):
 p,r=inputs;rows=m.read_csv(p,m.PROVIDER_COLUMNS);write(p,sorted(m.PROVIDER_COLUMNS),rows*2)
 assert m.audit_date('2023-10-24',p,r,{})['status']=='DUPLICATE_IDS'
def test_duplicate_reference(inputs):
 p,r=inputs;rows=m.read_csv(r,m.REFERENCE_COLUMNS);write(r,sorted(m.REFERENCE_COLUMNS),rows*2)
 assert m.audit_date('2023-10-24',p,r,{})['status']=='DUPLICATE_IDS'
def test_missing_evidence(inputs):
 p,r=inputs;rows=m.read_csv(r,m.REFERENCE_COLUMNS);rows[0]['evidence_sha256']='';write(r,sorted(m.REFERENCE_COLUMNS),rows)
 assert m.audit_date('2023-10-24',p,r,{'8':'DEN','14':'LAL'})['status']=='REFERENCE_EVIDENCE_INCOMPLETE'
def test_empty_not_approved(inputs):
 p,r=inputs;write(p,sorted(m.PROVIDER_COLUMNS),[]);write(r,sorted(m.REFERENCE_COLUMNS),[])
 assert m.audit_date('2023-10-24',p,r,{})['status']=='EMPTY_BOTH_UNVERIFIED'
def test_missing_official(inputs):
 p,r=inputs;rows=m.read_csv(r,m.REFERENCE_COLUMNS);rows.append(dict(rows[0],official_nba_game_id='0022300062',home_team='GSW',away_team='PHX'));write(r,sorted(m.REFERENCE_COLUMNS),rows)
 assert m.audit_date('2023-10-24',p,r,{'8':'DEN','14':'LAL'})['status']=='COVERAGE_MISMATCH'
def test_naive_time_invalid():assert m.timestamp('2023-10-24T23:30:00') is None
def test_unsafe_path(inputs,tmp_path):
 p,r=inputs;write(tmp_path/'date_manifest.csv',['date','phase','provider_csv','reference_csv','selection_reason'],[dict(date='2023-10-24',phase='regular',provider_csv='../secret',reference_csv='',selection_reason='test')]);write(tmp_path/'cross.csv',['provider_team_id','official_team','evidence_url','reviewed_by'],[dict(provider_team_id='8',official_team='DEN',evidence_url='x',reviewed_by='x')]);
 with pytest.raises(ValueError,match='UNSAFE_MANIFEST_PATH'):m.run(tmp_path/'date_manifest.csv',tmp_path/'cross.csv',tmp_path)
