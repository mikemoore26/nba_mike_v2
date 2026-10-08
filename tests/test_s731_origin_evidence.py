import csv,hashlib,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/p0_s4/s7_31'))
from run_s7_31 import audit,EVIDENCE
FIELDS=['candidate_number','player_name','player_id','event_date','to_team','from_team','source_sha256','validation_flags']
def setup(tmp,rows=None,ev=None):
 r=tmp/'review.csv';e=tmp/'evidence.csv'
 with r.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows if rows is not None else [dict(candidate_number='1',player_name='Example Player',player_id='123',event_date='2026-02-05',to_team='NYK',from_team='',source_sha256='a'*64,validation_flags='ORIGIN_NOT_ESTABLISHED')])
 with e.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=EVIDENCE);w.writeheader();w.writerows(ev or [])
 return r,e
def evidence(tmp,origin='BOS',quote='Example Player traded from Boston',sha=None):
 p=tmp/'independent.txt';p.write_text(quote)
 return dict(candidate_number='1',player_id='123',event_date='2026-02-05',from_team=origin,to_team='NYK',source_url='https://example.com/trade',snapshot_path=str(p),snapshot_sha256=sha or hashlib.sha256(p.read_bytes()).hexdigest(),verbatim_excerpt=quote)
def test_empty_evidence(tmp_path):
 r,e=setup(tmp_path);x=audit(r,e,tmp_path/'out');assert x['no_independent_evidence']==1 and x['qualified_s726_events']==0
def test_located_still_review(tmp_path):
 r,e=setup(tmp_path,ev=[evidence(tmp_path)]);x=audit(r,e,tmp_path/'out');assert x['source_excerpt_located_review']==1 and x['qualified_s726_events']==0
def test_hash_reject(tmp_path):
 r,e=setup(tmp_path,ev=[evidence(tmp_path,sha='0'*64)]);assert audit(r,e,tmp_path/'out')['evidence_rejected']==1
def test_missing_player_reject(tmp_path):
 r,e=setup(tmp_path,ev=[evidence(tmp_path,quote='Boston trades someone')]);assert audit(r,e,tmp_path/'out')['evidence_rejected']==1
def test_no_invented_origin(tmp_path):
 r,e=setup(tmp_path);audit(r,e,tmp_path/'out');text=(tmp_path/'out/s7_31_review.csv').read_text();assert 'SOURCE_EXCERPT_LOCATED_REVIEW' not in text
def test_conflicting_origins(tmp_path):
 ev=[evidence(tmp_path,'BOS'),evidence(tmp_path,'LAL')];r,e=setup(tmp_path,ev=ev);assert audit(r,e,tmp_path/'out')['conflicting_source_assertions']==1
def test_unknown_candidate_reject(tmp_path):
 row=evidence(tmp_path);row['candidate_number']='2';r,e=setup(tmp_path,ev=[row]);
 with pytest.raises(ValueError,match='Unknown'):audit(r,e,tmp_path/'out')
def test_duplicate_candidates_reject(tmp_path):
 row=dict(candidate_number='1',player_name='Example Player',player_id='123',event_date='2026-02-05',to_team='NYK',from_team='',source_sha256='a'*64,validation_flags='');r,e=setup(tmp_path,rows=[row,row]);
 with pytest.raises(ValueError,match='Duplicate'):audit(r,e,tmp_path/'out')
def test_tracker_not_independent(tmp_path):
 row=evidence(tmp_path);row['source_url']='https://www.nba.com/news/2025-26-nba-trade-tracker';r,e=setup(tmp_path,ev=[row]);assert audit(r,e,tmp_path/'out')['evidence_rejected']==1
