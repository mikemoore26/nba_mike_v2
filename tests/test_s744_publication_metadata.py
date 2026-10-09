import csv,hashlib,importlib.util,json
from pathlib import Path
import pytest
SRC=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_44/run_s7_44.py'
spec=importlib.util.spec_from_file_location('s744',SRC);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_meta_and_jsonld():
 html='<meta property="article:published_time" content="2026-02-05T10:00:00Z"><script type="application/ld+json">{"datePublished":"2026-02-05","dateModified":"2026-02-07"}</script>'
 got=m.extract(html)
 assert ('article:published_time','2026-02-05T10:00:00Z','HTML_META') in got
 assert ('datePublished','2026-02-05','JSON_LD') in got
 assert len(got)==3

def test_invalid_date():assert m.normalize('2026-02-30')==''
def test_unrelated_date():assert m.normalize('Feb 5 2026')==''
def test_iso_datetime():assert m.normalize('2026-02-05T12:00:00Z')=='2026-02-05'
def test_empty_html():assert m.extract('<html></html>')==[]
def test_nested_jsonld():assert ('datePublished','2026-02-05','JSON_LD') in m.extract('<script type="application/ld+json">{"@graph":[{"datePublished":"2026-02-05"}]}</script>')
def test_bad_jsonld():assert m.extract('<script type="application/ld+json">{bad}</script>')==[]
def test_time_element():assert ('time.datetime','2026-02-05','HTML_TIME') in m.extract('<time datetime="2026-02-05">February 5</time>')
def fixture(tmp_path,sha_override=None,url='https://www.nba.com/news/a',verified='false'):
 objects=tmp_path/'objects';objects.mkdir()
 raw=b'<meta property="article:published_time" content="2026-02-05T10:00:00Z">'
 sha=hashlib.sha256(raw).hexdigest();(objects/(sha+'.html')).write_bytes(raw)
 r={'candidate_number':'1','player_name':'Test Player','player_id':'1','tracker_event_date':'2026-02-05','origin_candidate':'ATL','destination_candidate':'GSW','article_url':url,'article_sha256':sha_override or sha,'review_status':'DIRECTION_EVENT_UNRESOLVED','historical_publication_verified':verified,'origin_team_verified':'false'}
 p=tmp_path/'in.csv'
 with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(r));w.writeheader();w.writerow(r)
 return p,objects,tmp_path/'out'
def test_run_remains_blocked(tmp_path):
 p,o,out=fixture(tmp_path);report=m.run(p,o,out)
 assert report['articles_with_candidate_dates']==1
 assert report['event_dates_verified']==0 and not report['historical_publication_verified']
 assert (out/'s7_44_article_inventory.json').exists()
def test_hash_tamper_fails(tmp_path):
 p,o,out=fixture(tmp_path);next(o.iterdir()).write_bytes(b'changed')
 with pytest.raises(ValueError,match='SHA mismatch'):m.run(p,o,out)
def test_unapproved_url_fails(tmp_path):
 p,o,out=fixture(tmp_path,url='https://example.com/article')
 with pytest.raises(ValueError,match='Non-official'):m.run(p,o,out)
def test_upstream_promotion_fails(tmp_path):
 p,o,out=fixture(tmp_path,verified='true')
 with pytest.raises(ValueError,match='Unexpected'):m.run(p,o,out)
def test_missing_object_fails(tmp_path):
 p,o,out=fixture(tmp_path);next(o.iterdir()).unlink()
 with pytest.raises(FileNotFoundError):m.run(p,o,out)
