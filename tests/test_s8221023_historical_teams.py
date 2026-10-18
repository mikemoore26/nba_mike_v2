import importlib.util
from pathlib import Path
import pytest

P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_23/run_s8_22_10_23.py'
spec=importlib.util.spec_from_file_location('s23',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def candidate(team='BOS'):
    return [{'record_id':'P-001','raw_name':'Example','candidate_nba_person_id':'12','report_team':team}]
def ev(team='BOS', start='2023-11-01',end='2023-11-30',eid='E1'):
    return {'evidence_id':eid,'nba_person_id':'12','team_abbreviation':team,'valid_from':start,'valid_to':end}

def test_empty(): assert m.classify(candidate(),[])[0]['classification']=='NO_DATED_EVIDENCE'
def test_match_not_certified():
    r=m.classify(candidate(),[ev()])[0]
    assert r['classification']=='DATED_TEAM_MATCH_UNCERTIFIED' and r['historical_team_verified']=='NO'
def test_mismatch(): assert m.classify(candidate(),[ev('NYK')])[0]['classification']=='DATED_TEAM_MISMATCH_REVIEW'
def test_conflict(): assert m.classify(candidate(),[ev(),ev('NYK',eid='E2')])[0]['classification']=='CONFLICTING_DATED_TEAM_EVIDENCE'
def test_out_of_range(): assert m.classify(candidate(),[ev(start='2023-12-01',end='2023-12-31')])[0]['classification']=='NO_DATED_EVIDENCE'
def test_other_id(): assert m.classify(candidate(),[{**ev(),'nba_person_id':'99'}])[0]['classification']=='NO_DATED_EVIDENCE'
def test_sha(): assert len(m.sha(b'x'))==64
def test_duplicate_candidates():
    with pytest.raises(ValueError):m.validate_candidates([{'record_id':'P-001'}]*44)
def test_csv_roundtrip(tmp_path):
    p=tmp_path/'a.csv';p.write_bytes(m.csvbytes([{'a':'x','b':'y'}],['a','b']));assert m.csvrows(p)==[{'a':'x','b':'y'}]
def test_immutable_conflict(tmp_path):
    p=tmp_path/'a';m.write_immutable(p,b'one');m.write_immutable(p,b'one')
    with pytest.raises(ValueError):m.write_immutable(p,b'two')
def test_bad_evidence_schema(tmp_path):
    p=tmp_path/'e.csv';p.write_text('id,team\n1,BOS\n')
    with pytest.raises(ValueError):m.load_evidence(p)
def test_evidence_valid(tmp_path):
    p=tmp_path/'e.csv';d={k:'' for k in m.EVIDENCE_FIELDS};d.update({'evidence_id':'E1','nba_person_id':'12','team_abbreviation':'BOS','valid_from':'2023-11-01','valid_to':'2023-11-30'})
    p.write_bytes(m.csvbytes([d],m.EVIDENCE_FIELDS));rows,h=m.load_evidence(p);assert len(rows)==1 and len(h)==64
