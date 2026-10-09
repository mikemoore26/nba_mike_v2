import csv,importlib.util,tempfile,unittest
from pathlib import Path
M=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_6/run_s8_22_6.py'
spec=importlib.util.spec_from_file_location('s8226',M);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();p=Path(self.tmp.name);self.p=p/'games.csv';self.m=p/'map.csv'
  with self.p.open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=mod.FIELDS);w.writeheader()
   for id,home,away,time in [('a','7','8','2023-10-24T23:30:00Z'),('b','9','10','2023-10-25T02:00:00Z')]:
    w.writerow(dict(provider='balldontlie',provider_game_id=id,game_date='2023-10-24',home_provider_team_id=home,away_provider_team_id=away,tipoff_utc=time))
  self.write_map([('7','DEN'),('8','LAL'),('9','GSW'),('10','PHX')])
 def tearDown(self):self.tmp.cleanup()
 def write_map(self,pairs):
  with self.m.open('w',newline='') as f:
   w=csv.writer(f);w.writerow(['provider_team_id','official_team','evidence_url','reviewed_by']);w.writerows([(a,b,'','') for a,b in pairs])
 def test_two_candidates(self):
  r,rows=mod.run(self.p,self.m,'2023-10-24');self.assertEqual(r['matched_candidates'],2);self.assertEqual(r['decision'],'BLOCK_TRAINING');self.assertEqual(rows[0]['match_status'],'CANDIDATE_MATCH_REVIEW_REQUIRED')
 def test_missing_mapping(self):
  self.write_map([]);r,rows=mod.run(self.p,self.m,'2023-10-24');self.assertEqual(r['matched_candidates'],0)
 def test_bad_team(self):
  self.write_map([('7','BAD')]);self.assertRaises(ValueError,mod.run,self.p,self.m,'2023-10-24')
 def test_duplicate_team_id(self):
  self.write_map([('7','DEN'),('7','LAL')]);self.assertRaises(ValueError,mod.run,self.p,self.m,'2023-10-24')
 def test_unsupported_date(self):self.assertRaises(ValueError,mod.run,self.p,self.m,'2026-10-10')
 def test_empty_provider(self):
  self.p.write_text(','.join(mod.FIELDS)+'\n');r,_=mod.run(self.p,self.m,'2023-10-24');self.assertEqual(r['missing_official_games'],['0022300061','0022300062'])
 def test_wrong_date(self):
  s=self.p.read_text().replace('2023-10-24,7','2023-10-23,7');self.p.write_text(s);self.assertRaises(ValueError,mod.run,self.p,self.m,'2023-10-24')
 def test_duplicate_game(self):
  s=self.p.read_text().replace('balldontlie,b,','balldontlie,a,');self.p.write_text(s);self.assertRaises(ValueError,mod.run,self.p,self.m,'2023-10-24')
 def test_time_disagree(self):
  self.p.write_text(self.p.read_text().replace('2023-10-24T23:30:00Z','2023-10-24T23:50:00Z'));_,rows=mod.run(self.p,self.m,'2023-10-24');self.assertEqual(rows[0]['match_status'],'TIPOFF_DISAGREES')
 def test_missing_time(self):
  self.p.write_text(self.p.read_text().replace('2023-10-24T23:30:00Z',''));_,rows=mod.run(self.p,self.m,'2023-10-24');self.assertEqual(rows[0]['match_status'],'TIPOFF_MISSING_OR_INVALID')
 def test_no_promotion(self):
  r,_=mod.run(self.p,self.m,'2023-10-24');self.assertFalse(r['training_eligible']);self.assertEqual(r['provider_crosswalk'],'CANDIDATE_ONLY')
if __name__=='__main__':unittest.main()
