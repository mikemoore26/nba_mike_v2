import importlib.util
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_20/run_s8_22_10_20.py'
spec=importlib.util.spec_from_file_location('s8221020',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def fixtures():
    ledger=[];cor=[]
    for i in range(44):
        rid=f'P-{i+1:03d}';name='Wright, Delon' if i==0 else f'Surname, Person{i}'
        ledger.append(dict(record_id=rid,record_type='PLAYER',name_or_notice_candidate=name,team_candidate='WAS'))
        cor.append(dict(record_id=rid,raw_name=name,local_name_corrob='YES',match_class='LOCAL_NAME_MATCH'))
    ledger.extend(dict(record_id=f'T-{i}',record_type='TEAM_SUBMISSION') for i in range(10))
    return ledger,cor
def registry(rows):return {'resultSets':[{'name':'CommonAllPlayers','headers':['PERSON_ID','DISPLAY_FIRST_LAST','TEAM_ABBREVIATION'],'rowSet':rows}]}
@pytest.mark.parametrize('value,expected',[('Wright, Delon','delon wright'),('Delon Wright','delon wright'),('José Álvarez','jose alvarez'),('Karl-Anthony Towns','karl anthony towns')])
def test_normalized(value,expected):assert m.normalized(value)==expected
def test_no_registry():
    l,c=fixtures();rows=m.reconcile(l,c)
    assert len(rows)==44 and all(x['registry_match_class']=='REGISTRY_NOT_SUPPLIED' and x['candidate_nba_person_id']=='' for x in rows)
def test_unique_team_candidate():
    l,c=fixtures();rows=m.reconcile(l,c,m.parse_registry(registry([[123,'Delon Wright','WAS']])))
    assert rows[0]['registry_match_class']=='NAME_TEAM_CANDIDATE' and rows[0]['candidate_nba_person_id']=='123'
    assert rows[0]['player_identity_certified']=='NO'
def test_team_mismatch():
    l,c=fixtures();rows=m.reconcile(l,c,m.parse_registry(registry([[123,'Delon Wright','MIA']])))
    assert rows[0]['registry_match_class']=='TEAM_MISMATCH_REVIEW' and not rows[0]['candidate_nba_person_id']
def test_ambiguous():
    l,c=fixtures();rows=m.reconcile(l,c,m.parse_registry(registry([[123,'Delon Wright','WAS'],[456,'Delon Wright','WAS']])))
    assert rows[0]['registry_match_class']=='AMBIGUOUS_REGISTRY_NAME'
def test_registry_missing_team():
    l,c=fixtures();rows=m.reconcile(l,c,m.parse_registry(registry([[123,'Delon Wright','']])))
    assert rows[0]['registry_match_class']=='REGISTRY_TEAM_MISSING'
def test_no_name_match():
    l,c=fixtures();rows=m.reconcile(l,c,m.parse_registry(registry([[123,'Someone Else','WAS']])))
    assert rows[0]['registry_match_class']=='NO_REGISTRY_NAME_MATCH'
def test_reject_unsupported_registry():
    with pytest.raises(ValueError):m.parse_registry({'players':[{'id':123}]})
def test_reject_malformed_registry():
    with pytest.raises(ValueError):m.parse_registry(registry([[123,'Delon Wright']]))
def test_reject_bad_id():
    with pytest.raises(ValueError):m.parse_registry(registry([['abc','Delon Wright','WAS']]))
def test_reject_uncorroborated():
    l,c=fixtures();c[0]['local_name_corrob']='NO'
    with pytest.raises(ValueError,match='not established'):m.reconcile(l,c)
def test_reject_duplicate_record():
    l,c=fixtures();c[1]['record_id']=c[0]['record_id']
    with pytest.raises(ValueError,match='Duplicate'):m.reconcile(l,c)
def test_never_certify():
    l,c=fixtures();rows=m.reconcile(l,c,m.parse_registry(registry([[123,'Delon Wright','WAS']])))
    assert all(r['player_identity_certified']=='NO' and r['injury_status_certified']=='NO' and r['historical_asof_certified']=='NO' for r in rows)
