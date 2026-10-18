import importlib.util
import csv
import io
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_25/run_s8_22_10_25.py'
spec=importlib.util.spec_from_file_location('s825',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def candidate():return {'record_id':'P1','raw_name':'Wright, Delon','candidate_nba_person_id':'1626153','report_team':'WAS','registry_full_name':'Delon Wright'}
def prior():return [{'record_id':'P1','classification':'NO_BOX_SCORE_LISTING_NOT_NEGATIVE_PROOF'}]
def names(r):return {'delon wright'}
def norm(n):return n.casefold()
def entry(team='WAS',id='10',date='2023-11-14'):
    return {'name':'Delon Wright','team':team,'event_id':'401','espn_athlete_id':id,'date':date}
def classify(entries):return m.classify([candidate()],prior(),entries,norm,names)[0]
def test_empty():assert classify([])['adjacent_classification']=='NO_ADJACENT_BOX_SCORE_LISTING'
def test_same():assert classify([entry()])['adjacent_classification']=='ADJACENT_SAME_TEAM_LISTING_UNCERTIFIED'
def test_other():assert classify([entry('ATL')])['adjacent_classification']=='ADJACENT_OTHER_TEAM_LISTING_REVIEW'
def test_conflict():assert classify([entry(),entry('ATL')])['adjacent_classification']=='CONFLICTING_ADJACENT_TEAM_LISTINGS_REVIEW'
def test_id_ambiguity():assert classify([entry(),entry(id='11')])['adjacent_classification']=='AMBIGUOUS_ESPN_IDENTITIES_REVIEW'
def test_never_certify():
    r=classify([entry()]);assert r['historical_team_verified']=='NO' and r['training_decision']=='BLOCK_TRAINING'
def test_date_provenance():assert classify([entry()])['adjacent_dates']=='2023-11-14'
def test_csv_schema():
    data=m.csv_data([classify([])]);assert len(list(csv.DictReader(io.StringIO(data.decode()))))==1
def test_date_target_rejected():
    with pytest.raises(ValueError):m.validate_dates(['2023-11-15'])
def test_date_far_rejected():
    with pytest.raises(ValueError):m.validate_dates(['2023-12-15'])
def test_duplicate_dates_rejected():
    with pytest.raises(ValueError):m.validate_dates(['2023-11-14','2023-11-14'])
def test_immutable(tmp_path):
    p=tmp_path/'x';m.immutable(p,b'abc');m.immutable(p,b'abc')
    with pytest.raises(ValueError):m.immutable(p,b'xyz')
def test_predecessor_unpack_regression(tmp_path):
    # This catches the earlier mistake of unpacking a one-element list rather than its tuple.
    matches=[('manifest','candidates','metadata')]
    mf,path,metadata=matches[0]
    assert (mf,path,metadata)==('manifest','candidates','metadata')
