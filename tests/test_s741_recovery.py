import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

PATH=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_41/run_s7_41.py'
spec=importlib.util.spec_from_file_location('s741',PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_norm_accents():assert m.contains('Kristaps Porzingis','Kristaps Porziņģis')
def test_player_boundary():assert not m.contains('AJ Johnsonson','AJ Johnson')
def test_direction_acquired():assert m.direction('Charlotte Hornets acquired Malaki Branham from Washington Wizards in a trade','Malaki Branham')==('ACQUIRED_FROM','WAS','CHA')
def test_direction_traded():assert m.direction('Golden State Warriors traded Buddy Hield to Atlanta Hawks in a deal','Buddy Hield')==('TRADED_TO','GSW','ATL')
def test_no_direction_from_mentions():assert m.direction('Buddy Hield joins Atlanta Hawks after Golden State Warriors news','Buddy Hield')[0]=='NONE'
def test_no_direction_ambiguous():assert m.direction('Hawks acquired Buddy Hield from Golden State Warriors and Atlanta Hawks','Buddy Hield')[0]=='NONE'
def test_extract_headline_and_article():
    raw=b'<html><head><meta property="og:title" content="Hornets acquire Tyus Jones from Orlando Magic"></head><body><nav><p>Tyus Jones traded in navigation</p></nav><article><h1>Hornets acquire Tyus Jones from Orlando Magic</h1><p>Charlotte Hornets acquired Tyus Jones from Orlando Magic in trade.</p></article><footer>junk</footer></body></html>'
    extracted=m.extract(raw)
    assert ('ARTICLE_PARAGRAPH','Charlotte Hornets acquired Tyus Jones from Orlando Magic in trade.') in extracted
    assert all('navigation' not in text for _,text in extracted)
def test_fallback_page_paragraph():assert ('PAGE_PARAGRAPH','Hawks acquired Buddy Hield from Golden State Warriors') in m.extract(b'<p>Hawks acquired Buddy Hield from Golden State Warriors</p>')

def fixture(tmp_path, html, overrides=None):
    obj=tmp_path/'objects';obj.mkdir();raw=html.encode();sha=hashlib.sha256(raw).hexdigest();(obj/(sha+'.html')).write_bytes(raw)
    row={'candidate_number':'1','player_name':'Malaki Branham','player_id':'123','event_date':'2026-02-05','to_team':'CHA','article_url':'https://www.nba.com/hornets/news/example','capture_status':'CAPTURED','article_sha256':sha,'article_bytes':str(len(raw)),'historical_publication_verified':'false','origin_team_verified':'false'}
    row.update(overrides or {});csvpath=tmp_path/'review.csv'
    with csvpath.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(row));w.writeheader();w.writerow(row)
    return csvpath,obj,tmp_path/'results'

def test_run_direction_review_only(tmp_path):
    c,o,out=fixture(tmp_path,'<article><h1>Charlotte Hornets acquired Malaki Branham from Washington Wizards in trade</h1></article>')
    r=m.run(c,o,out);assert r['direction_proposals']==1 and r['origin_teams_verified']==0 and r['status_totals_reconcile']
    rows=list(csv.DictReader((out/'s7_41_review.csv').open()));assert rows[0]['origin_candidate']=='WAS' and rows[0]['destination_candidate']=='CHA'
    assert rows[0]['historical_publication_verified']=='false'
def test_tamper_fail_closed(tmp_path):
    c,o,out=fixture(tmp_path,'<h1>Hornets acquired Malaki Branham from Wizards</h1>')
    next(o.iterdir()).write_text('tampered')
    with pytest.raises(ValueError,match='SHA256'):m.run(c,o,out)
def test_verified_upstream_rejected(tmp_path):
    c,o,out=fixture(tmp_path,'<p>test</p>',{'origin_team_verified':'true'})
    with pytest.raises(ValueError,match='verified'):m.run(c,o,out)
def test_destination_conflict_rejected(tmp_path):
    c,o,out=fixture(tmp_path,'<h1>Atlanta Hawks acquired Malaki Branham from Washington Wizards in trade</h1>')
    r=m.run(c,o,out);assert r['direction_proposals']==0
    assert 'TRACKER_DESTINATION_CONFLICT' in (out/'s7_41_review.csv').read_text()
def test_missing_object_fail_closed(tmp_path):
    c,o,out=fixture(tmp_path,'<p>test</p>');next(o.iterdir()).unlink()
    with pytest.raises(ValueError,match='Missing source'):m.run(c,o,out)
def test_dedup_headline(tmp_path):
    c,o,out=fixture(tmp_path,'<meta property="og:title" content="Charlotte Hornets acquired Malaki Branham from Washington Wizards"><h1>Charlotte Hornets acquired Malaki Branham from Washington Wizards</h1>')
    r=m.run(c,o,out);assert r['review_rows']==1
