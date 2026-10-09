import csv,hashlib,importlib.util,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_35/run_s7_35.py'
spec=importlib.util.spec_from_file_location('s735',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_rss_valid():
 d=m.inspect(b'<rss><channel><item><link>https://www.nba.com/news/a</link></item></channel></rss>');assert d['official_links']==1
def test_html_detected():assert m.classify(b'<!doctype html><html></html>')=='HTML_NOT_RSS'
def test_invalid_xml():assert m.classify(b'not xml')=='INVALID_XML'
def test_non_official():
 d=m.inspect(b'<rss><channel><item><link>https://example.com/story</link></item></channel></rss>');assert d['rejected_links']==1
def test_filtered_tracker():assert not m.official('https://www.nba.com/news/2025-26-nba-trade-tracker')
def test_allow_news():assert m.official('https://www.nba.com/news/real-story')
def test_no_links():assert m.inspect(b'<rss><channel><item><title>x</title></item></channel></rss>')['rss_item_links']==0
def test_wrapped_not_official():assert not m.official('https://www.bing.com/ck/a?u=https://www.nba.com/news/a')
def test_missing_hash(tmp_path):
 inp=tmp_path/'in.csv';inp.write_text('candidate_number,player_name,search_sha256,capture_status\n1,Test,,NO_OFFICIAL_LINKS\n');r=m.run(inp,tmp_path/'obj',tmp_path/'out');assert r['integrity_ok']==0

def test_hash_integrity(tmp_path):
 raw=b'<rss><channel><item><link>https://www.nba.com/news/a</link></item></channel></rss>';sha=hashlib.sha256(raw).hexdigest();o=tmp_path/'objects';o.mkdir();(o/(sha+'.xml')).write_bytes(raw);inp=tmp_path/'in.csv';inp.write_text(f'candidate_number,player_name,search_sha256,capture_status\n1,Test,{sha},NO_OFFICIAL_LINKS\n');r=m.run(inp,o,tmp_path/'out');assert r['total_official_links']==1 and r['eligible_for_asof_training'] is False
