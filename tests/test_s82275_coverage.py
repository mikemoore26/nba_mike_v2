import csv,json,sys,tempfile,unittest
from pathlib import Path
from importlib.util import spec_from_file_location,module_from_spec
P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_7_5/run_s8_22_7_5.py'
spec=spec_from_file_location('s82275',P);m=module_from_spec(spec);spec.loader.exec_module(m)
class CoverageTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name)
  self.manifest=self.root/'manifest.csv';self.crosswalk=self.root/'crosswalk.csv'
  self.write(self.crosswalk,['provider_team_id','official_team','evidence_url','reviewed_by'],[['8','DEN','https://api.balldontlie.io/v1/teams','USER'],['14','LAL','https://api.balldontlie.io/v1/teams','USER']])
 def write(self,path,fields,rows):
  with path.open('w',newline='') as f:
   w=csv.writer(f);w.writerow(fields);w.writerows(rows)
 def manifest_for(self,date='2023-10-24',p='p.csv',ref='r.csv',announcement=''):
  self.write(self.manifest,m.FIELDS,[[date,'regular',p,ref,announcement,'','','','']])
 def provider(self,rows=None):
  self.write(self.root/'p.csv',['game_date','away_provider_team_id','home_provider_team_id','provider_game_id','tipoff_utc'],rows if rows is not None else [['2023-10-24','14','8','11','2023-10-24T23:30:00Z']])
 def reference(self,rows=None):
  self.write(self.root/'r.csv',['game_date','evidence_sha256','evidence_retrieved_utc','away_team','home_team','official_nba_game_id','source_url','tipoff_utc'],rows if rows is not None else [['2023-10-24','a'*64,'2026-10-10T00:00:00Z','LAL','DEN','0022300061','https://www.nba.com/game/lal-vs-den-0022300061','2023-10-24T23:30:00Z']])
 def result(self):return m.audit(self.root,self.manifest,self.crosswalk)[1][0]
 def test_missing_provider(self):
  self.manifest_for();self.assertEqual(self.result()['status'],'PROVIDER_SNAPSHOT_MISSING')
 def test_provider_missing_reference(self):
  self.provider();self.manifest_for(ref='');self.assertEqual(self.result()['status'],'INDEPENDENT_REFERENCE_MISSING')
 def test_positive_match_not_certified(self):
  self.provider();self.reference();self.manifest_for();x=self.result();self.assertEqual(x['status'],'CANDIDATE_PROVIDER_GAME_MATCH_DATE_COVERAGE_MISSING');self.assertFalse(x['training_eligible'])
 def test_announcement_agreement(self):
  self.provider();self.reference();a={'date':'2023-10-24','row_set_agreement':True,'announcement_rows':1,'game_reference_rows':1,'conflicts':[],'unsupported_quotes':[],'coverage_quote_present':True,'decision':'BLOCK_TRAINING'}
  (self.root/'a.json').write_text(json.dumps(a));self.manifest_for(announcement='a.json');self.assertEqual(self.result()['status'],'CANDIDATE_ANNOUNCEMENT_AGREEMENT_REVIEW_REQUIRED')
 def test_announcement_conflict(self):
  self.provider();self.reference();(self.root/'a.json').write_text('{}');self.manifest_for(announcement='a.json');self.assertEqual(self.result()['status'],'ANNOUNCEMENT_REPORT_CONFLICT')
 def test_zero_rows_never_certified(self):
  self.provider([]);self.manifest_for();self.assertEqual(self.result()['status'],'ZERO_PROVIDER_ROWS_NEGATIVE_EVIDENCE_REVIEW_REQUIRED')
 def test_duplicate_provider(self):
  row=['2023-10-24','14','8','11','2023-10-24T23:30:00Z'];self.provider([row,row]);self.manifest_for();self.assertEqual(self.result()['status'],'PROVIDER_DUPLICATE_IDS')
 def test_reference_duplicate(self):
  self.provider();row=['2023-10-24','a'*64,'2026-10-10T00:00:00Z','LAL','DEN','0022300061','https://www.nba.com/game/lal-vs-den-0022300061','2023-10-24T23:30:00Z'];self.reference([row,row]);self.manifest_for();self.assertEqual(self.result()['status'],'REFERENCE_DUPLICATE_IDS')
 def test_tipoff_conflict(self):
  self.provider([['2023-10-24','14','8','11','2023-10-25T03:30:00Z']]);self.reference();self.manifest_for();self.assertEqual(self.result()['status'],'PROVIDER_REFERENCE_CONFLICT')
 def test_unsafe_path(self):
  self.manifest_for(p='../bad.csv')
  with self.assertRaises(ValueError):self.result()
 def test_empty_reference(self):
  self.provider();self.reference([]);self.manifest_for();self.assertEqual(self.result()['status'],'EMPTY_REFERENCE_UNVERIFIED')
 def test_invalid_date(self):
  self.manifest_for(date='2025-01-01')
  with self.assertRaises(ValueError):self.result()
 def test_missing_dates_filled(self):
  self.manifest_for();self.assertEqual(len(m.audit(self.root,self.manifest,self.crosswalk)[1]),5)
 def test_source_receipt_missing(self):
  self.assertEqual(m.valid_receipt(self.root,None,'2023-10-24'),(False,'RECEIPT_MISSING'))
if __name__=='__main__':unittest.main()
