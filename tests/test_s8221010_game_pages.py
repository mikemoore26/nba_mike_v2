import importlib.util
from pathlib import Path
import tempfile
import unittest
P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_10/run_s8_22_10_10.py'
s=importlib.util.spec_from_file_location('gamepage',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
DATE='2023-11-15'; MATCH='DAL@WAS'; GID='0022300192'
def html(t):return ('<html><head><title>'+t+'</title></head><body>Game</body></html>').encode()
GOOD=html('Dallas Mavericks vs Washington Wizards Nov 15, 2023 Game Summary | NBA.com')
class Test(unittest.TestCase):
 def test_title(self):self.assertEqual(m.inspect(GOOD,DATE,MATCH,GID)[0],'TITLE_MATCH_REVIEW_REQUIRED')
 def test_wrong_team(self):self.assertEqual(m.inspect(html('Dallas Mavericks vs Chicago Bulls Nov 15, 2023'),DATE,MATCH,GID)[0],'TEAM_TITLE_MISMATCH')
 def test_wrong_date(self):self.assertEqual(m.inspect(html('Dallas Mavericks vs Washington Wizards Nov 16, 2023'),DATE,MATCH,GID)[0],'DATE_TITLE_NOT_CONFIRMED')
 def test_no_title(self):self.assertEqual(m.inspect(b'<html></html>',DATE,MATCH,GID)[0],'MISSING_TITLE')
 def test_bad_utf8(self):self.assertEqual(m.inspect(b'\xff',DATE,MATCH,GID)[0],'INVALID_HTML')
 def test_social_title(self):self.assertEqual(m.inspect(b'<meta property="og:title" content="Dallas Mavericks vs Washington Wizards Nov 15, 2023">',DATE,MATCH,GID)[0],'TITLE_MATCH_REVIEW_REQUIRED')
 def test_bad_count(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(ValueError):m.process([],Path(t),False,1)
 def test_offline_eight(self):
  games=[('DAL@WAS','0022300192'),('NYK@ATL','0022300193'),('BOS@PHI','0022300194'),('MIL@TOR','0022300195'),('ORL@CHI','0022300196'),('MIN@PHX','0022300197'),('SAC@LAL','0022300198'),('CLE@POR','0022300199')]
  rows=[dict(game_date=DATE,away_at_home=k,provisional_nba_game_id=v,game_id_status='UNVERIFIED_PROVISIONAL') for k,v in games]
  with tempfile.TemporaryDirectory() as t:
   result=m.process(rows,Path(t),False,1)
   self.assertEqual(len(result),8);self.assertTrue(all(x['content_status']=='NOT_CHECKED' for x in result))
 def test_fetch_archives(self):
  games=[('DAL@WAS','0022300192'),('NYK@ATL','0022300193'),('BOS@PHI','0022300194'),('MIL@TOR','0022300195'),('ORL@CHI','0022300196'),('MIN@PHX','0022300197'),('SAC@LAL','0022300198'),('CLE@POR','0022300199')]
  rows=[dict(game_date=DATE,away_at_home=k,provisional_nba_game_id=v,game_id_status='UNVERIFIED_PROVISIONAL') for k,v in games]
  def fetch(url,timeout):
   slug=url.rsplit('/',1)[-1];a,h=slug.split('-vs-')[0],slug.split('-vs-')[1].split('-')[0]
   aa,hh=a.upper(),h.upper()
   return 200,html(f'{m.NAMES[aa]} vs {m.NAMES[hh]} Nov 15, 2023 Game Summary')
  with tempfile.TemporaryDirectory() as t:
   result=m.process(rows,Path(t),True,1,fetch)
   self.assertTrue(all(x['content_status']=='TITLE_MATCH_REVIEW_REQUIRED' for x in result))
   self.assertTrue(all(Path(x['snapshot_path']).exists() for x in result))
   again=m.process(rows,Path(t),False,1)
   self.assertTrue(all(x['acquisition_status']=='REUSED_EXISTING_SNAPSHOT' for x in again))
if __name__=='__main__':unittest.main()
