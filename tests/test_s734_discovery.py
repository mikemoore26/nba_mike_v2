import csv,hashlib,importlib.util
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_34/run_s7_34.py'
spec=importlib.util.spec_from_file_location('s734',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_canonical():
 assert m.canonical('https://www.nba.com/news/some-trade?x=1')=='https://www.nba.com/news/some-trade'
 assert m.canonical('https://evil.com/news/some-trade') is None
 assert m.canonical('https://www.nba.com/news/2025-26-nba-trade-tracker') is None
def test_rss_filters():
 raw=b'<rss><channel><item><link>https://www.nba.com/news/a</link></item><item><link>https://evil.com/news/b</link></item><item><link>https://www.nba.com/news/a</link></item></channel></rss>'
 assert m.rss_links(raw)==['https://www.nba.com/news/a']
def test_bad_rss():assert m.rss_links(b'not xml')==[]
def test_unicode_name():assert m.has_name('D’Angelo Russell joined','D\'Angelo Russell')
def test_no_surname_only():assert not m.has_name('Russell traded','D’Angelo Russell')
def test_analyze_positive():assert m.analyze(b'<p>Anthony Davis was traded by the Mavericks.</p>','Anthony Davis')=='RELEVANT_REVIEW'
def test_analyze_no_player():assert m.analyze(b'<p>Someone was traded.</p>','Anthony Davis')=='REJECT_PLAYER_NOT_FOUND'
def test_analyze_no_trade():assert m.analyze(b'<p>Anthony Davis scored 25 points.</p>','Anthony Davis')=='REJECT_NO_TRANSACTION_CONTEXT'
def test_query_targeted():
 q=m.query_for({'player_name':'Anthony Davis','to_team':'WAS','event_date':'2026-02-05'})
 assert 'bing.com/search?' in q and 'site%3Anba.com' in q
def test_store_hash(tmp_path):
 sha=m.store(b'hello',tmp_path,'.html');assert sha==hashlib.sha256(b'hello').hexdigest()
 assert (tmp_path/(sha+'.html')).read_bytes()==b'hello'
def test_fixture_integration(tmp_path):
 csvpath=tmp_path/'review.csv';fields=['candidate_number','player_name','player_id','event_date','to_team','from_team']
 with csvpath.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerow(dict(candidate_number='1',player_name='Anthony Davis',player_id='203076',event_date='2026-02-05',to_team='WAS',from_team=''))
 fix=tmp_path/'fixtures';fix.mkdir();link='https://www.nba.com/news/anthony-davis-trade';(fix/'1.xml').write_text(f'<rss><channel><item><link>{link}</link></item></channel></rss>')
 (fix/('article_'+hashlib.sha256(link.encode()).hexdigest()+'.html')).write_text('<p>Anthony Davis was traded to the Wizards.</p>')
 report=m.acquire(csvpath,tmp_path/'out',fixture_dir=fix)
 assert report['candidate_players_with_relevant_leads']==1
 assert report['origin_teams_verified']==0
 assert report['eligible_for_asof_training'] is False
