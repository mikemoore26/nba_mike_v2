import csv,hashlib,importlib.util,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_38/run_s7_38.py'
spec=importlib.util.spec_from_file_location('s738',P);s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
class TestS738(unittest.TestCase):
 def test_official(self):self.assertTrue(s.official('https://www.nba.com/news/anthony-davis-trade'))
 def test_team(self):self.assertTrue(s.official('https://www.nba.com/hawks/news/transaction-2026'))
 def test_spoof(self):self.assertFalse(s.official('https://www.nba.com.evil.org/news/a'))
 def test_http(self):self.assertFalse(s.official('http://www.nba.com/news/a'))
 def test_query(self):self.assertFalse(s.official('https://www.nba.com/news/a?x=1'))
 def test_credentials(self):self.assertFalse(s.official('https://nba.com@evil.org/news/a'))
 def test_traversal(self):self.assertFalse(s.official('https://www.nba.com/news/../admin'))
 def test_relevant(self):self.assertEqual(s.relevant('Anthony Davis traded to the Wizards','Anthony Davis')[0],'RELEVANT_REVIEW_ONLY')
 def test_no_player(self):self.assertEqual(s.relevant('LeBron James was traded','Anthony Davis')[0],'PLAYER_NOT_FOUND')
 def test_no_transaction(self):self.assertEqual(s.relevant('Anthony Davis scored 20 points','Anthony Davis')[0],'TRANSACTION_TERMS_NOT_FOUND')
 def test_accents(self):self.assertEqual(s.relevant('Kristaps Porzingis acquired by Warriors','Kristaps Porziņģis')[0],'RELEVANT_REVIEW_ONLY')
 def test_script_ignored(self):self.assertEqual(s.relevant(s.parse_article(b'<html><script>Anthony Davis traded</script><p>Basketball news</p></html>')[1],'Anthony Davis')[0],'PLAYER_NOT_FOUND')
 def test_integration(self):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td);src=t/'input.csv';url='https://www.nba.com/news/anthony-davis-trade';row=dict.fromkeys(s.FIELDS,'');row.update(candidate_number='7',player_name='Anthony Davis',player_id='123',event_date='2026-02-05',to_team='WAS',article_url=url,review_status='OFFICIAL_LINK_REVIEW_ONLY',source_sha256='a'*64,historical_publication_verified='false')
   with src.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=s.FIELDS);w.writeheader();w.writerow(row)
   raw=b'<html><title>NBA</title><p>Anthony Davis traded in blockbuster deal.</p></html>'
   report=s.run(src,t/'out',fetcher=lambda u:raw,delay=0)
   self.assertEqual(report['relevant_review_leads'],1);self.assertEqual(report['origin_teams_verified'],0)
   self.assertEqual(report['eligible_for_asof_training'],False)
   self.assertTrue((t/'out'/'objects'/(hashlib.sha256(raw).hexdigest()+'.html')).exists())
 def test_reject_invalid_input(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad.csv';p.write_text('foo,bar\na,b\n')
   with self.assertRaisesRegex(ValueError,'schema'):s.load_review(p)
 def test_fail_closed_fetch(self):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td);src=t/'input.csv';row=dict.fromkeys(s.FIELDS,'');row.update(candidate_number='1',player_name='Anthony Davis',article_url='https://www.nba.com/news/anthony-davis',review_status='OFFICIAL_LINK_REVIEW_ONLY',source_sha256='a'*64,historical_publication_verified='false')
   with src.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=s.FIELDS);w.writeheader();w.writerow(row)
   def bad(u):raise OSError('offline')
   report=s.run(src,t/'out',fetcher=bad,delay=0);self.assertEqual(report['status_counts']['FETCH_FAILED:NOT_EVALUATED'],1)
if __name__=='__main__':unittest.main()
