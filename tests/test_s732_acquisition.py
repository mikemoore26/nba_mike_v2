import csv,hashlib,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/p0_s4/s7_32'))
from run_s7_32 import article_url,discover,safe_capture,acquire,read_review
FIELDS=['candidate_number','player_name','player_id','event_date','to_team','from_team','validation_flags']
def fixture(tmp,rows=None):
 p=tmp/'review.csv'
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows if rows is not None else [dict(candidate_number='1',player_name='Example Player',player_id='123',event_date='2026-02-05',to_team='NYK',from_team='',validation_flags='ORIGIN_NOT_ESTABLISHED')])
 return p
def test_url_allowlist():
 assert article_url('https://www.nba.com/news/sample-trade')=='https://www.nba.com/news/sample-trade'
 assert article_url('https://evil.com/news/trade') is None
 assert article_url('http://www.nba.com/news/trade') is None
 assert article_url('https://www.nba.com/news/2025-26-nba-trade-tracker') is None
 assert article_url('https://www.nba.com.evil.com/news/x') is None
def test_discovery_dedup():
 assert discover('<a href="/news/trade-a">A</a><a href="https://www.nba.com/news/trade-a">A</a>')==['https://www.nba.com/news/trade-a']
def test_capture_hash(tmp_path):
 p,h=safe_capture('https://www.nba.com/news/sample',tmp_path,fetcher=lambda u:(b'<html>proof</html>',u))
 assert Path(p).exists() and h==hashlib.sha256(b'<html>proof</html>').hexdigest()
def test_capture_reject_redirect(tmp_path):
 with pytest.raises(ValueError,match='redirect'):safe_capture('https://www.nba.com/news/sample',tmp_path,fetcher=lambda u:(b'abc','https://evil.com/news/sample'))
def test_no_links_is_not_success(tmp_path):
 p=fixture(tmp_path);d=tmp_path/'fixture';d.mkdir();(d/'1.html').write_text('<html>Search has no articles</html>')
 x=acquire(p,tmp_path/'out',search_fixture_dir=d);assert x['no_article_links']==1 and x['origin_teams_verified']==0
def test_article_capture_still_unverified(tmp_path,monkeypatch):
 import run_s7_32
 p=fixture(tmp_path);d=tmp_path/'fixture';d.mkdir();(d/'1.html').write_text('<a href="/news/example-player-traded">link</a>')
 monkeypatch.setattr(run_s7_32,'safe_capture',lambda u,o,fetcher=None:(str(tmp_path/'article.html'),'a'*64))
 x=acquire(p,tmp_path/'out',search_fixture_dir=d)
 assert x['captured_article_rows']==1 and x['origin_teams_verified']==0 and x['qualified_s726_events']==0
 assert (tmp_path/'out'/'s7_32_capture.csv').exists()
def test_duplicate_candidates_fail(tmp_path):
 row=dict(candidate_number='1',player_name='A',player_id='123',event_date='2026-02-05',to_team='NYK',from_team='',validation_flags='')
 with pytest.raises(ValueError,match='Duplicate'):read_review(fixture(tmp_path,[row,row]))
def test_ineligible_skipped(tmp_path):
 p=fixture(tmp_path,[dict(candidate_number='1',player_name='A',player_id='',event_date='2026-02-05',to_team='NYK',from_team='',validation_flags='')]);x=acquire(p,tmp_path/'out')
 assert x['attempted_candidates']==0
def test_limit_reject(tmp_path):
 with pytest.raises(ValueError):acquire(fixture(tmp_path),tmp_path/'out',limit=0)
