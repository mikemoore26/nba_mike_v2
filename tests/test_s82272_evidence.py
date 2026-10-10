import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_7_2'))
from run_s8_22_7_2 import archive_bytes,normalize,update_manifest,safe_url,sha

class EvidenceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)
  self.meta=archive_bytes(self.root,'2023-10-24','https://www.nba.com/game/lal-vs-den-0022300061',b'<html>official</html>')
  self.receipt=self.root/self.meta['evidence_path'].replace('source.bin','receipt.json')
  self.rows=self.root/'review.csv'
  self.rows.write_text('game_date,official_nba_game_id,home_team,away_team,tipoff_utc\n2023-10-24,0022300061,DEN,LAL,2023-10-24T23:30:00+00:00\n')
 def test_archive_digest(self):self.assertEqual(self.meta['sha256'],sha(b'<html>official</html>'))
 def test_receipt_has_no_asof_claim(self):self.assertFalse(self.meta['pre_game_publication_verified'])
 def test_normalize(self):
  x=normalize(self.root,'2023-10-24',self.receipt,self.rows)
  self.assertEqual(x['rows'],1);self.assertFalse(x['training_eligible'])
 def test_reference_columns(self):
  x=normalize(self.root,'2023-10-24',self.receipt,self.rows)
  with (self.root/x['reference_path']).open() as f:
   rows=list(csv.DictReader(f))
  self.assertEqual(rows[0]['evidence_sha256'],self.meta['sha256'])
 def test_reject_tamper(self):
  (self.root/self.meta['evidence_path']).write_bytes(b'tampered')
  with self.assertRaisesRegex(ValueError,'EVIDENCE_HASH'):normalize(self.root,'2023-10-24',self.receipt,self.rows)
 def test_reject_date(self):
  with self.assertRaisesRegex(ValueError,'DATE_MISMATCH'):normalize(self.root,'2023-10-25',self.receipt,self.rows)
 def test_reject_empty(self):
  self.rows.write_text('game_date,official_nba_game_id,home_team,away_team,tipoff_utc\n')
  with self.assertRaisesRegex(ValueError,'EMPTY_REFERENCE'):normalize(self.root,'2023-10-24',self.receipt,self.rows)
 def test_reject_duplicate(self):
  self.rows.write_text(self.rows.read_text()+self.rows.read_text().splitlines()[1]+'\n')
  with self.assertRaisesRegex(ValueError,'DUPLICATE'):normalize(self.root,'2023-10-24',self.receipt,self.rows)
 def test_reject_bad_time(self):
  self.rows.write_text(self.rows.read_text().replace('2023-10-24T23:30:00+00:00','not-a-time'))
  with self.assertRaisesRegex(ValueError,'INVALID_TIPOFF'):normalize(self.root,'2023-10-24',self.receipt,self.rows)
 def test_reject_non_nba_domain(self):
  with self.assertRaises(ValueError):safe_url('https://evil.com/a')
 def test_reject_http(self):
  with self.assertRaises(ValueError):safe_url('http://www.nba.com/a')
 def test_manifest_no_overwrite(self):
  d=self.root/'research/p0_s8/s8_22_7';d.mkdir(parents=True)
  (d/'date_manifest.csv').write_text('date,phase,provider_csv,reference_csv,selection_reason\n2023-10-24,regular,,existing.csv,opening\n')
  with self.assertRaisesRegex(ValueError,'NO_OVERWRITE'):update_manifest(self.root,'2023-10-24','any.csv')
 def test_manifest_update(self):
  d=self.root/'research/p0_s8/s8_22_7';d.mkdir(parents=True)
  (d/'date_manifest.csv').write_text('date,phase,provider_csv,reference_csv,selection_reason\n2023-10-24,regular,,,opening\n')
  x=normalize(self.root,'2023-10-24',self.receipt,self.rows)
  update_manifest(self.root,'2023-10-24',x['reference_path'])
  self.assertIn(x['reference_path'],(d/'date_manifest.csv').read_text())
 def test_reject_credentials_in_url(self):
  with self.assertRaises(ValueError):safe_url('https://user:password@www.nba.com/game')
if __name__=='__main__':unittest.main()
