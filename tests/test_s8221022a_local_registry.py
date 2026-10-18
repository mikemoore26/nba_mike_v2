import importlib.util
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_22a/run_s8_22_10_22a.py'
s=importlib.util.spec_from_file_location('localregistry',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def norm(s):return s.lower().replace(',','').strip()
def ledger():return [{'record_id':f'P-{i:03}','record_type':'PLAYER','name_or_notice_candidate':f'Player {i}','team_candidate':'BOS'} for i in range(1,45)]+[{'record_id':f'T-{i:03}','record_type':'TEAM'} for i in range(1,11)]
def corroboration():return [{'record_id':f'P-{i:03}','raw_name':f'Player {i}','local_name_corrob':'YES','match_class':'LOCAL_NAME_MATCH'} for i in range(1,45)]
def registry():return [{'id':i,'full_name':f'Player {i}'} for i in range(1,45)]
def test_unique():
 r=m.candidates(ledger(),corroboration(),registry(),norm);assert len(r)==44;assert all(x['match_class']=='UNIQUE_NAME_ID_CANDIDATE' for x in r);assert all(x['player_identity_certified']=='NO' for x in r)
def test_ambiguous():
 r=registry()+[{'id':1000,'full_name':'Player 1'}];assert m.candidates(ledger(),corroboration(),r,norm)[0]['match_class']=='AMBIGUOUS_NAME_MATCH'
def test_missing():assert m.candidates(ledger(),corroboration(),registry()[1:],norm)[0]['match_class']=='NO_NAME_MATCH'
def test_corrupt_name():
 c=corroboration();c[0]['raw_name']='Wrong'
 with pytest.raises(ValueError):m.candidates(ledger(),c,registry(),norm)
def test_uncorroborated():
 c=corroboration();c[0]['local_name_corrob']='NO'
 with pytest.raises(ValueError):m.candidates(ledger(),c,registry(),norm)
def test_missing_row():
 with pytest.raises(ValueError):m.candidates(ledger(),corroboration()[:-1],registry(),norm)
def test_duplicate_record():
 with pytest.raises(ValueError):m.candidates(ledger(),corroboration()+[corroboration()[0]],registry(),norm)
def test_immutable(tmp_path):
 p=tmp_path/'raw';m.immutable(p,b'abc');m.immutable(p,b'abc')
 with pytest.raises(ValueError):m.immutable(p,b'def')
def test_digest():assert len(m.digest(b'abc'))==64
def test_name_only():
 r=m.candidates(ledger(),corroboration(),registry(),norm);assert all(x['historical_team_verified']=='NO' for x in r)
