import csv,hashlib,importlib.util,json
from pathlib import Path
import pytest
PATH=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_47/run_s7_47.py'
spec=importlib.util.spec_from_file_location('s747',PATH);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_hash():assert m.digest(b'abc')==hashlib.sha256(b'abc').hexdigest()
def test_url_match():assert m.norm_url('https://www.nba.com/x/')==m.norm_url('https://nba.com/x')
def test_url_mismatch():assert m.norm_url('https://nba.com/a')!=m.norm_url('https://nba.com/b')
def test_timestamp_valid():assert m.capture_dt('20260205060140') is not None
def test_timestamp_invalid():assert m.capture_dt('20260231060140') is None
def test_cutoff_tz_required():
 with pytest.raises(ValueError):m.parse_cutoff('2026-02-05T08:00:00')
def test_cutoff_utc():assert m.parse_cutoff('2026-02-05T08:00:00Z').hour==8
def test_html_removes_navigation():assert 'unrelated' not in m.extract_text(b'<nav>unrelated</nav><p>article</p>')
def test_html_visible():assert 'article' in m.extract_text(b'<p>article</p>')
def test_alias():assert m.team_mentioned('The Golden State Warriors','GSW')
def test_alias_no_partial():assert not m.team_mentioned('The wizardry','WAS')
def test_local_claim():
 s=b'<article><p>Atlanta Hawks acquire Buddy Hield from Golden State Warriors in a trade.</p></article>'
 assert m.evaluate_claim(s,'Buddy Hield','GSW','ATL')[0]=='LOCAL_DIRECTION_CANDIDATE'
def test_player_only():assert m.evaluate_claim(b'<p>Buddy Hield played today.</p>','Buddy Hield','GSW','ATL')[0]=='PLAYER_MENTION_WITHOUT_DIRECTION'
def test_no_proposal():assert m.evaluate_claim(b'abc','Buddy Hield','','ATL')[0]=='NO_DIRECTION_PROPOSAL'
def test_missing_capture_is_not_absence(tmp_path):
 inp=tmp_path/'input.csv';pr=tmp_path/'p.csv';out=tmp_path/'out'
 with inp.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['article_url','archive_capture_status','archive_timestamp','captured_sha256']);w.writeheader();w.writerow({'article_url':'https://nba.com/a','archive_capture_status':'CAPTURE_FETCH_FAILED'})
 with pr.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['article_url','player_name','origin_candidate','destination_candidate']);w.writeheader();w.writerow({'article_url':'https://nba.com/a','player_name':'A','origin_candidate':'GSW','destination_candidate':'ATL'})
 r=m.process(inp,pr,tmp_path/'objects',out)
 assert r['evidence_status_counts']['NO_SAVED_CAPTURE']==1
 assert r['eligible_for_asof_training'] is False
