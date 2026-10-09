import csv
import hashlib
import importlib.util
from pathlib import Path

P=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_50/run_s7_50.py'
spec=importlib.util.spec_from_file_location('s750',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_extract_jsonld_and_paragraph():
    b=b'<script type="application/ld+json">{"headline":"Atlanta Hawks acquire Buddy Hield from Golden State","articleBody":"Atlanta Hawks acquired Buddy Hield from Golden State."}</script><p>Other text</p>'
    e=m.extract(b)
    assert ('JSONLD_HEADLINE','Atlanta Hawks acquire Buddy Hield from Golden State') in e
    assert ('P','Other text') in e

def test_direction_positive():assert m.direction('Atlanta Hawks acquire Buddy Hield from Golden State','Buddy Hield','GSW','ATL')=='FULL_TEXT_DIRECTION_CANDIDATE'
def test_direction_no_player():assert m.direction('Atlanta Hawks acquire someone from Golden State','Buddy Hield','GSW','ATL')=='MAPPING_INCOMPLETE'
def test_direction_cooccurrence():assert m.direction('Buddy Hield spoke about Atlanta Hawks and Golden State Warriors','Buddy Hield','GSW','ATL')=='COOCCURRENCE_ONLY'
def test_direction_incomplete():assert m.direction('Atlanta Hawks acquire Anthony Davis from Dallas','Anthony Davis','','ATL')=='MAPPING_INCOMPLETE'
def test_stage_pending():assert m.stage('trade is pending league approval')=='PENDING_APPROVAL_LANGUAGE'
def test_stage_reported():assert m.stage('the teams agreed to a trade')=='REPORTED_OR_AGREED_LANGUAGE'
def test_stage_announcement():assert m.stage('Hawks announced the acquisition')=='ANNOUNCEMENT_LANGUAGE_UNVERIFIED'
def test_url_exact():assert m.valid_url('https://www.nba.com/a','https://www.nba.com/a/')
def test_url_mismatch():assert not m.valid_url('https://www.nba.com/a','https://evil.example/a')
def test_no_nav_text():assert not any('Ghost Player' in s for _,s in m.extract(b'<nav><p>Ghost Player</p></nav><p>Actual body</p>'))
def test_no_duplicate():assert len(m.extract(b'<p>same</p><p>same</p>'))==1

def test_process_offline(tmp_path):
    obj=tmp_path/'objects';obj.mkdir();blob=b'<html><h1>Atlanta Hawks acquire Buddy Hield from Golden State</h1></html>';sha=hashlib.sha256(blob).hexdigest();(obj/(sha+'.html')).write_bytes(blob)
    def csvwrite(path,cols,rows):
        with path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
    i=tmp_path/'in.csv';a=tmp_path/'archive.csv';u='https://www.nba.com/hawks/news/test'
    csvwrite(i,['player_name','origin_candidate','destination_candidate','article_url','archive_timestamp','captured_sha256'],[dict(player_name='Buddy Hield',origin_candidate='GSW',destination_candidate='ATL',article_url=u,archive_timestamp='20260206005216',captured_sha256=sha)])
    csvwrite(a,['article_url','archive_timestamp','captured_sha256','archive_original_url'],[dict(article_url=u,archive_timestamp='20260206005216',captured_sha256=sha,archive_original_url=u)])
    r=m.process(i,a,obj,tmp_path/'out');assert r['full_text_direction_candidates']==1;assert not r['eligible_for_asof_training']

def test_process_bad_hash(tmp_path):
    i=tmp_path/'i.csv';a=tmp_path/'a.csv'
    i.write_text('player_name,origin_candidate,destination_candidate,article_url,archive_timestamp,captured_sha256\nA,GSW,ATL,https://www.nba.com/a,20260201,'+'a'*64+'\n')
    a.write_text('article_url,archive_timestamp,captured_sha256,archive_original_url\n')
    o=tmp_path/'obj';o.mkdir();(o/('a'*64+'.html')).write_bytes(b'bad')
    r=m.process(i,a,o,tmp_path/'out');assert r['integrity_counts']=={'HASH_MISMATCH':1}

def test_html_entities():assert ('P','A & B') in m.extract(b'<p>A &amp; B</p>')
