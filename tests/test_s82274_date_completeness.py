import json,sys,tempfile,unittest,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_7_4'))
from run_s8_22_7_4 import audit,evidence,parse_rows,official_url
class TestDateCompleteness(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name)
  data=b'official nba schedule 0022300061 0022300062'
  rel='research/p0_s8/s8_22_7_2/evidence/2023-10-24/abc/source.bin'
  p=self.root/rel;p.parent.mkdir(parents=True);p.write_bytes(data)
  self.receipt=p.parent/'receipt.json'
  self.receipt.write_text(json.dumps({'date':'2023-10-24','source_url':'https://www.nba.com/schedule','retrieved_utc':'2026-10-10T00:00:00Z','sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'evidence_path':rel}))
  self.datecsv=self.root/'date.csv';self.refcsv=self.root/'ref.csv'
  self.rows='game_date,official_nba_game_id,home_team,away_team,tipoff_utc\n2023-10-24,0022300061,DEN,LAL,2023-10-24T23:30:00Z\n2023-10-24,0022300062,GSW,PHX,2023-10-25T02:00:00Z\n'
  self.datecsv.write_text(self.rows);self.refcsv.write_text(self.rows)
 def runaudit(self):return audit(self.root,'2023-10-24',self.receipt,self.datecsv,self.refcsv)
 def test_agreement_is_not_certified(self):
  r=self.runaudit();self.assertTrue(r['row_set_agreement']);self.assertEqual(r['date_completeness'],'NOT_CERTIFIED')
 def test_report_written(self):self.assertTrue((self.root/self.runaudit()['report_path']).exists())
 def test_no_training(self):self.assertFalse(self.runaudit()['training_eligible'])
 def test_source_missing_id(self):
  self.receipt.write_text(self.receipt.read_text().replace('schedule','schedule'))
  self.datecsv.write_text(self.rows.replace('0022300062','0022300063'))
  self.assertEqual(self.runaudit()['missing_game_ids_in_archived_date_source'],['0022300063'])
 def test_extra_reference(self):
  self.datecsv.write_text('game_date,official_nba_game_id,home_team,away_team,tipoff_utc\n2023-10-24,0022300061,DEN,LAL,2023-10-24T23:30:00Z\n')
  self.assertEqual(self.runaudit()['extra_in_individual_reference'],['0022300062'])
 def test_missing_reference(self):
  self.refcsv.write_text('game_date,official_nba_game_id,home_team,away_team,tipoff_utc\n2023-10-24,0022300061,DEN,LAL,2023-10-24T23:30:00Z\n')
  self.assertEqual(self.runaudit()['missing_from_individual_reference'],['0022300062'])
 def test_team_conflict(self):
  self.refcsv.write_text(self.rows.replace(',DEN,LAL,',',NYK,LAL,'))
  self.assertTrue(self.runaudit()['field_conflicts'])
 def test_tipoff_conflict(self):
  self.refcsv.write_text(self.rows.replace('23:30:00Z','23:40:00Z'))
  self.assertTrue(self.runaudit()['field_conflicts'])
 def test_tipoff_tolerance(self):
  self.refcsv.write_text(self.rows.replace('23:30:00Z','23:34:00Z'))
  self.assertFalse(self.runaudit()['field_conflicts'])
 def test_tampered_bytes(self):
  (self.root/json.loads(self.receipt.read_text())['evidence_path']).write_bytes(b'bad')
  with self.assertRaisesRegex(ValueError,'INTEGRITY'):self.runaudit()
 def test_empty_not_proof(self):
  self.datecsv.write_text('game_date,official_nba_game_id,home_team,away_team,tipoff_utc\n')
  with self.assertRaisesRegex(ValueError,'EMPTY_DATE'):self.runaudit()
 def test_duplicate(self):
  self.datecsv.write_text(self.rows+self.rows.splitlines()[1]+'\n')
  with self.assertRaisesRegex(ValueError,'DUPLICATE'):self.runaudit()
 def test_bad_host(self):
  with self.assertRaises(ValueError):official_url('https://www.nba.com.evil.org/schedule')
 def test_wrong_date(self):
  with self.assertRaisesRegex(ValueError,'RECEIPT_DATE'):audit(self.root,'2023-10-25',self.receipt,self.datecsv,self.refcsv)
if __name__=='__main__':unittest.main()
