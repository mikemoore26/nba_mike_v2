import csv,importlib.util
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_26/run_s7_26.py'
spec=importlib.util.spec_from_file_location('s726',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def row(**kw):
 d=dict(player_id='123',player_name='Test Player',effective_date='2026-03-20',event_type='TRADE',from_team='NYK',to_team='BKN',source_name='Official',source_url='https://example.com/source',source_document_sha256='a'*64,source_published_utc='2026-03-20T10:00:00+00:00',retrieved_utc='2026-10-08T10:00:00+00:00',evidence_id='one');d.update(kw);return d
def write(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=m.FIELDS);w.writeheader();w.writerows(rows)
def test_valid_event():assert m.validate(row()) is None
def test_missing_id():assert m.validate(row(player_id=''))=='INVALID_IDENTITY'
def test_invalid_date():assert m.validate(row(effective_date='2026-02-30'))=='INVALID_DATE'
def test_bad_trade():assert m.validate(row(to_team='NYK'))=='INVALID_TRANSFER'
def test_missing_source():assert m.validate(row(source_url='http://example.com'))=='MISSING_SOURCE_PROVENANCE'
def test_future_publication():assert m.validate(row(source_published_utc='2027-01-01T00:00:00+00:00'))=='INVALID_SOURCE_TIMES'
def test_empty(tmp_path):
 p=tmp_path/'events.csv';write(p,[]);v=m.process(p,tmp_path/'out');assert v['accepted_events']==0 and not v['eligible_for_asof_training']
def test_same_day_conflict(tmp_path):
 p=tmp_path/'events.csv';write(p,[row(),row(to_team='BOS',evidence_id='two')]);v=m.process(p,tmp_path/'out');assert v['same_day_conflict_rows']==2 and v['accepted_events']==0
def test_chronology_not_roster(tmp_path):
 p=tmp_path/'events.csv';write(p,[row()]);v=m.process(p,tmp_path/'out');assert v['accepted_events']==1 and v['roster_intervals_promoted']==0
