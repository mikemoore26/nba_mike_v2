import csv,hashlib,importlib.util,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_37/run_s7_37.py'
spec=importlib.util.spec_from_file_location('s737',P);s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
class TestS737(unittest.TestCase):
 def test_official_news(self):self.assertEqual(s.official_article('/news/jonathan-kuminga-trade'),'https://www.nba.com/news/jonathan-kuminga-trade')
 def test_official_team_news(self):self.assertEqual(s.official_article('https://www.nba.com/hawks/news/atlanta-hawks-acquire-buddy-hield'),'https://www.nba.com/hawks/news/atlanta-hawks-acquire-buddy-hield')
 def test_host_spoof(self):self.assertEqual(s.official_article('https://www.nba.com.evil.org/news/anthony-davis'),'')
 def test_credentials(self):self.assertEqual(s.official_article('https://nba.com@evil.org/news/anthony-davis'),'')
 def test_http(self):self.assertEqual(s.official_article('http://www.nba.com/news/anthony-davis'),'')
 def test_tracker_excluded(self):self.assertEqual(s.official_article('/news/2025-26-nba-trade-tracker'),'')
 def test_category_excluded(self):self.assertEqual(s.official_article('/news/category/top-stories'),'')
 def test_query_excluded(self):self.assertEqual(s.official_article('/news/anthony-davis?redirect=1'),'')
 def test_player_url(self):self.assertEqual(s.match_player('Anthony Davis','https://www.nba.com/news/anthony-davis-trade','Wizards'),'PLAYER_TOKENS_IN_URL')
 def test_player_anchor(self):self.assertEqual(s.match_player('Buddy Hield','https://www.nba.com/hawks/news/transaction-2026','Buddy Hield traded'),'PLAYER_TOKENS_IN_ANCHOR')
 def test_single_name_insufficient(self):self.assertEqual(s.match_player('Anthony Davis','https://www.nba.com/news/anthony-trade','Wizards'),'')
 def test_accent(self):self.assertEqual(s.match_player('Kristaps Porziņģis','https://www.nba.com/news/kristaps-porzingis-trade','Warriors'),'PLAYER_TOKENS_IN_URL')
 def test_integration_and_fail_closed(self):
  with tempfile.TemporaryDirectory() as t:
   t=Path(t);raw=b'<html><a href="/news/anthony-davis-trade">Wizards</a><a href="https://fake-nba.com/news/anthony-davis">fake</a></html>';source=t/'source.html';source.write_bytes(raw);sha=hashlib.sha256(raw).hexdigest();review=t/'review.csv'
   with review.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=sorted(s.CANDIDATE_FIELDS));w.writeheader();w.writerow(dict(candidate_number='1',player_name='Anthony Davis',player_id='123',event_date='2026-02-05',to_team='WAS',from_team='',source_sha256=sha))
   report=s.discover(source,review,t/'out',sha);self.assertEqual(report['candidates_with_direct_name_links'],1);self.assertEqual(report['official_article_urls_in_tracker'],1);self.assertEqual(report['origin_teams_verified'],0)
   with self.assertRaisesRegex(ValueError,'SHA'):s.discover(source,review,t/'out','0'*64)
   review.write_text(review.read_text().replace(sha,'1'*64))
   with self.assertRaisesRegex(ValueError,'SHA'):s.discover(source,review,t/'out',sha)
if __name__=='__main__':unittest.main()
