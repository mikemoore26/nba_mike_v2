import csv,hashlib,json,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/p0_s4/s7_29'))
from run_s7_29 import normalized,parse_directory,resolve,fetch

def directory(rows):return json.dumps({'resultSets':[{'name':'CommonAllPlayers','headers':['PERSON_ID','DISPLAY_FIRST_LAST'],'rowSet':rows}]}).encode()
def fixture(tmp_path,items):
 html=tmp_path/'source.html';html.write_text('<html>original</html>');sha=hashlib.sha256(html.read_bytes()).hexdigest();csvfile=tmp_path/'review.csv';fields=['candidate_number','event_date','player_name','source_sha256','review_reason','to_team','from_team']
 with csvfile.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for i,(name,reason) in enumerate(items,1):w.writerow(dict(candidate_number=i,event_date='2026-02-05',player_name=name,source_sha256=sha,review_reason=reason,to_team='NYK',from_team=''))
 return csvfile,html

def test_normalize_diacritics():assert normalized('José Alvarado')==normalized('Jose Alvarado')
def test_directory_exact():assert parse_directory(directory([[42,'Khris Middleton']]))[0]['khrismiddleton']=={'42'}
def test_missing_directory():
 with pytest.raises(ValueError):parse_directory(b'{}')
def test_empty_directory():
 with pytest.raises(ValueError):parse_directory(directory([]))
def test_duplicate_identity_ambiguous(tmp_path):
 c,h=fixture(tmp_path,[('Alex Smith','MISSING_OR_AMBIGUOUS_STABLE_ID')]);r=resolve(c,h,directory([[12,'Alex Smith'],[13,'Alex Smith']]),tmp_path/'out');assert r['ambiguous_ids']==1 and r['exact_unique_id_candidates']==0

def test_exact_and_nonplayer(tmp_path):
 c,h=fixture(tmp_path,[('Khris Middleton','NO_EXPLICIT_ORIGIN'),('','NON_PLAYER_ASSET'),('Unknown','NO_EXPLICIT_ORIGIN')]);r=resolve(c,h,directory([[42,'Khris Middleton']]),tmp_path/'out');assert (r['exact_unique_id_candidates'],r['non_player_assets'],r['unmatched_names'])==(1,1,1)
 assert r['qualified_s726_events']==0 and not r['eligible_for_asof_training']
def test_provenance_mismatch(tmp_path):
 c,h=fixture(tmp_path,[('Khris Middleton','')]);h.write_text('<html>changed</html>')
 with pytest.raises(ValueError,match='provenance'):resolve(c,h,directory([[42,'Khris Middleton']]),tmp_path/'out')
def test_no_fuzzy(tmp_path):
 c,h=fixture(tmp_path,[('Chris Middleton','')]);r=resolve(c,h,directory([[42,'Khris Middleton']]),tmp_path/'out');assert r['unmatched_names']==1
def test_invalid_player_id():
 with pytest.raises(ValueError):parse_directory(directory([['fake','Name']]))
def test_invalid_season():
 with pytest.raises(ValueError):fetch('2025-27')
