import csv,hashlib,sys,json
from pathlib import Path
from xml.sax.saxutils import escape
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/p0_s4/s7_36'))
from run_s7_36 import classify_url,unwrap_hint,audit
import pytest

def test_nba_news():assert classify_url('https://www.nba.com/news/some-story')[1]=='PASSES_EXISTING_FILTER'
def test_nba_other_path():assert classify_url('https://www.nba.com/team/roster')[1]=='OFFICIAL_PATH_EXCLUDED'
def test_nba_subdomain():assert classify_url('https://cdn.nba.com/abc')[1]=='SUBDOMAIN_EXCLUDED'
def test_external():assert classify_url('https://www.espn.com/nba/story')[0]=='EXTERNAL_UNVERIFIED'
def test_non_https():assert classify_url('http://www.nba.com/news/abc')[1]=='NOT_HTTPS'
def test_credentials():assert classify_url('https://x@www.nba.com/news/abc')[0]=='INVALID'
def test_wrapper():assert unwrap_hint('https://www.bing.com/ck?a=1&url=https%3A%2F%2Fwww.nba.com%2Fnews%2Fabc')=='https://www.nba.com/news/abc'
def test_nonwrapper():assert unwrap_hint('https://example.com/?url=https://www.nba.com')==''

def fixture(tmp_path,corrupt=False):
 root=tmp_path/'objects';root.mkdir();out=tmp_path/'out'
 raw=b'<rss><channel><item><title>Trade</title><link>https://www.nba.com/news/story</link></item><item><link>https://example.com/story</link></item></channel></rss>'
 sha=hashlib.sha256(raw).hexdigest();(root/(sha+'.xml')).write_bytes(raw+b'X' if corrupt else raw)
 review=tmp_path/'review.csv'
 with review.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['candidate_number','player_name','search_sha256']);w.writeheader();w.writerow({'candidate_number':'1','player_name':'Test Player','search_sha256':sha})
 return review,root,out

def test_audit_counts(tmp_path):
 review,root,out=fixture(tmp_path);r=audit(review,root,out)
 assert r['rss_links_classified']==2 and r['official_nba_links']==1
 assert (out/'s7_36_domain_counts.csv').is_file()
 assert len(list(csv.DictReader((out/'s7_36_url_review.csv').open())))==2

def test_corruption_fails_closed(tmp_path):
 review,root,out=fixture(tmp_path,True)
 with pytest.raises(ValueError,match='hash mismatch'):audit(review,root,out)
 assert not (out/'s7_36_report.json').exists()

def test_missing_object_fails_closed(tmp_path):
 review,root,out=fixture(tmp_path)
 for p in root.iterdir():p.unlink()
 with pytest.raises(FileNotFoundError):audit(review,root,out)
