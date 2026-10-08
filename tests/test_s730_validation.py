import csv,hashlib,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/p0_s4/s7_30'))
from run_s7_30 import audit
R=['candidate_number','player_name','event_date','to_team','from_team','source_sha256','review_reason']
I=R+['player_id','identity_status','directory_sha256']
def fixture(tmp_path,records):
 html=tmp_path/'source.html';html.write_text('<html>snapshot</html>');sha=hashlib.sha256(html.read_bytes()).hexdigest()
 rv=tmp_path/'review.csv';iv=tmp_path/'identity.csv'
 with rv.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=R);w.writeheader()
  for idx,(name,pid,to,frm,reason) in enumerate(records,1):w.writerow(dict(candidate_number=str(idx),player_name=name,event_date='2026-02-05',to_team=to,from_team=frm,source_sha256=sha,review_reason=reason))
 with iv.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=I);w.writeheader()
  for idx,(name,pid,to,frm,reason) in enumerate(records,1):w.writerow(dict(candidate_number=str(idx),player_name=name,event_date='2026-02-05',to_team=to,from_team=frm,source_sha256=sha,review_reason=reason,player_id=pid,identity_status='NON_PLAYER_ASSET' if 'NON_PLAYER_ASSET' in reason else 'EXACT_UNIQUE_ID_CANDIDATE' if pid else 'UNMATCHED_NAME',directory_sha256='a'*64))
 return rv,iv,html

def test_candidate_flags(tmp_path):
 r,i,h=fixture(tmp_path,[('Player','42','NYK','','NO_EXPLICIT_ORIGIN')]);x=audit(r,i,h,tmp_path/'out');assert x['identity_candidates']==1 and x['missing_origin']==1 and x['qualified_s726_events']==0

def test_nonplayer(tmp_path):
 r,i,h=fixture(tmp_path,[('','','NYK','','NON_PLAYER_ASSET')]);x=audit(r,i,h,tmp_path/'out');assert x['non_player_assets']==1

def test_unmatched(tmp_path):
 r,i,h=fixture(tmp_path,[('Unknown','','NYK','','MISSING_ID')]);x=audit(r,i,h,tmp_path/'out');assert x['unresolved_identities']==1

def test_same_day_multiple_destinations(tmp_path):
 r,i,h=fixture(tmp_path,[('Player','42','NYK','BOS',''),('Player','42','LAL','BOS','')]);x=audit(r,i,h,tmp_path/'out');assert x['multiple_destinations_same_day']==2

def test_same_team(tmp_path):
 r,i,h=fixture(tmp_path,[('Player','42','NYK','NYK','')]);assert audit(r,i,h,tmp_path/'out')['same_team_origin_destination']==1

def test_mismatch_fails(tmp_path):
 r,i,h=fixture(tmp_path,[('Player','42','NYK','BOS','')]);txt=i.read_text().replace('NYK','LAL');i.write_text(txt)
 with pytest.raises(ValueError,match='mismatch'):audit(r,i,h,tmp_path/'out')

def test_html_mutation_fails(tmp_path):
 r,i,h=fixture(tmp_path,[('Player','42','NYK','BOS','')]);h.write_text('<html>tampered</html>')
 with pytest.raises(ValueError,match='SHA-256'):audit(r,i,h,tmp_path/'out')

def test_bad_identity_fails(tmp_path):
 r,i,h=fixture(tmp_path,[('Player','42','NYK','BOS','')]);i.write_text(i.read_text().replace('42','abc'))
 with pytest.raises(ValueError,match='Invalid resolved identity'):audit(r,i,h,tmp_path/'out')

def test_empty_fails(tmp_path):
 r,i,h=fixture(tmp_path,[])
 with pytest.raises(ValueError,match='Empty'):audit(r,i,h,tmp_path/'out')
