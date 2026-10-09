import csv,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/p0_s4/s7_33'))
from run_s7_33 import visible,name_match,inspect_snapshot,audit

def make(tmp,body,player='Example Player',status='CAPTURED_REVIEW'):
 obj=tmp/'objects';obj.mkdir();raw=body.encode();sha=hashlib.sha256(raw).hexdigest();(obj/(sha+'.html')).write_bytes(raw)
 cap=tmp/'capture.csv';rev=tmp/'review.csv'
 with cap.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['candidate_number','player_name','player_id','event_date','to_team','article_url','snapshot_path','snapshot_sha256','capture_status']);w.writeheader();w.writerow(dict(candidate_number='1',player_name=player,player_id='123',event_date='2026-02-05',to_team='NYK',article_url='https://www.nba.com/news/example',snapshot_path='ignored',snapshot_sha256=sha,capture_status=status))
 with rev.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['candidate_number','player_name','player_id','from_team','validation_flags']);w.writeheader();w.writerow(dict(candidate_number='1',player_name=player,player_id='123',from_team='',validation_flags='ORIGIN_NOT_ESTABLISHED'))
 return cap,rev,obj,sha

def test_script_not_evidence():
 assert 'Phantom' not in visible(b'<script>Phantom</script><p>Visible</p>')
def test_name_exact_not_partial():
 assert name_match('AJ Johnson','AJ Johnson was traded')
 assert not name_match('AJ Johnson','Johnson was traded')
def test_name_unicode_apostrophe():
 assert name_match('D’Angelo Russell',"D'Angelo Russell")
def test_relevance_context(tmp_path):
 cap,rev,obj,sha=make(tmp_path,'<p>Example Player was traded to the Knicks.</p>')
 r=audit(cap,rev,obj,tmp_path/'out');assert r['candidate_players_with_nearby_trade_terms']==1 and r['origin_teams_verified']==0
 assert r['missing_origin_all_rows']==1 and r['eligible_missing_origin_with_numeric_id_and_name']==1
def test_unrelated_article_not_relevant(tmp_path):
 cap,rev,obj,sha=make(tmp_path,'<p>Other Player was traded to the Knicks.</p>')
 r=audit(cap,rev,obj,tmp_path/'out');assert r['audit_status_counts']['PLAYER_NOT_FOUND']==1
def test_player_mention_without_trade(tmp_path):
 cap,rev,obj,sha=make(tmp_path,'<p>Example Player scored 20 points.</p>')
 r=audit(cap,rev,obj,tmp_path/'out');assert r['audit_status_counts']['PLAYER_MENTION_ONLY']==1
def test_hash_mismatch(tmp_path):
 cap,rev,obj,sha=make(tmp_path,'<p>Example Player was traded.</p>')
 (obj/(sha+'.html')).write_text('tampered');r=audit(cap,rev,obj,tmp_path/'out');assert r['audit_status_counts']['HASH_MISMATCH']==1
def test_missing_snapshot(tmp_path):
 cap,rev,obj,sha=make(tmp_path,'<p>Example Player was traded.</p>')
 (obj/(sha+'.html')).unlink();r=audit(cap,rev,obj,tmp_path/'out');assert r['audit_status_counts']['SNAPSHOT_MISSING']==1
def test_no_promotion(tmp_path):
 cap,rev,obj,sha=make(tmp_path,'<p>Example Player traded from Lakers to Knicks.</p>')
 r=audit(cap,rev,obj,tmp_path/'out');assert r['qualified_s726_events']==0 and not r['eligible_for_asof_training']
def test_ineligible_difference(tmp_path):
 cap,rev,obj,sha=make(tmp_path,'<p>Example Player traded.</p>',player='')
 r=audit(cap,rev,obj,tmp_path/'out');assert r['excluded_from_acquisition_eligibility']==1
