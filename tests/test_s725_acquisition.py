import importlib.util
import json
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_25/run_s7_25.py'
spec=importlib.util.spec_from_file_location('s725',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def payload(rows):return json.dumps({'resultSets':[{'name':'CommonTeamRoster','headers':['PLAYER_ID','PLAYER'],'rowSet':rows}]}).encode()
def test_30_teams():assert len(m.TEAM_IDS)==30
def test_decode():assert list(m.decode_roster(json.loads(payload([[1,'A']]))))==[('1','A')]
def test_missing_set():
 with pytest.raises(ValueError,match='No CommonTeamRoster'):list(m.decode_roster({'resultSets':[]}))
def test_reject_duplicate(tmp_path):
 with pytest.raises(ValueError,match='Duplicate'):m.collect('NYK','2025-26',tmp_path,raw=payload([[1,'A'],[1,'B']]))
def test_reject_empty(tmp_path):
 with pytest.raises(ValueError,match='Empty roster'):m.collect('NYK','2025-26',tmp_path,raw=payload([]))
def test_reject_invalid_season(tmp_path):
 with pytest.raises(ValueError,match='Invalid season'):m.collect('NYK','2025-25',tmp_path,raw=payload([[1,'A']]))
def test_candidate_only_and_hash(tmp_path):
 raw=payload([[11,'A'],[12,'B']]);r=m.collect('NYK','2025-26',tmp_path,raw=raw)
 assert r['player_rows']==2 and not r['date_specific_verified'] and r['verified_injury_assignments']==0
 assert (tmp_path/'raw'/(r['source_sha256']+'.json')).read_bytes()==raw
 assert 'SEASON_ROSTER_CANDIDATE_ONLY' in (tmp_path/'s7_25_season_roster_candidates.csv').read_text()
def test_reject_malformed_row(tmp_path):
 with pytest.raises(ValueError,match='Mismatched'):m.collect('NYK','2025-26',tmp_path,raw=json.dumps({'resultSets':[{'name':'CommonTeamRoster','headers':['PLAYER_ID','PLAYER'],'rowSet':[[1]]}]}).encode())
