import csv
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
SRC=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_8/run_s8_22_8.py'
spec=importlib.util.spec_from_file_location('feasibility',SRC);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.manifest=self.root/'manifest.csv'
    def tearDown(self):self.tmp.cleanup()
    def rows(self,items):
        with self.manifest.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=mod.REQUIRED);w.writeheader();w.writerows(items)
    def test_blank_fail_closed(self):
        self.rows([]);r=mod.audit(self.root,self.manifest);self.assertTrue(all(x['status']=='NOT_ESTABLISHED' for x in r['categories'].values()));self.assertEqual(r['decision'],'BLOCK_TRAINING')
    def test_historical_time(self):
        self.assertIsNone(mod.parse_time('2023-11-15T10:00:00'));self.assertIsNotNone(mod.parse_time('2023-11-15T10:00:00Z'))
    def test_valid_candidate_never_certifies(self):
        p=self.root/'evidence.txt';p.write_text('original');sha=hashlib.sha256(p.read_bytes()).hexdigest()
        self.rows([dict.fromkeys(mod.REQUIRED,'')|dict(category='player_availability',source_name='archived',source_url='https://example.org/a',evidence_path='evidence.txt',sha256=sha,observed_utc='2023-11-15T10:00:00Z',event_tipoff_utc='2023-11-16T00:00:00Z',license_status='REVIEWED_PERMITTED',reviewer='human')]);r=mod.audit(self.root,self.manifest);self.assertEqual(r['categories']['player_availability']['status'],'CANDIDATE_MANUAL_REVIEW_REQUIRED');self.assertFalse(r['training_eligible'])
    def test_postgame_not_pregame(self):
        p=self.root/'evidence.txt';p.write_text('original');sha=hashlib.sha256(p.read_bytes()).hexdigest()
        self.rows([dict.fromkeys(mod.REQUIRED,'')|dict(category='starting_lineups',source_name='archived',source_url='https://example.org/a',evidence_path='evidence.txt',sha256=sha,observed_utc='2023-11-16T02:00:00Z',event_tipoff_utc='2023-11-16T00:00:00Z',license_status='REVIEWED_PERMITTED',reviewer='human')]);r=mod.audit(self.root,self.manifest);self.assertEqual(r['categories']['starting_lineups']['pregame_timestamp_rows'],0)
    def test_missing_source_fails(self):
        self.rows([dict.fromkeys(mod.REQUIRED,'')|dict(category='betting_markets',source_name='test',source_url='https://example.org',evidence_path='absent',sha256='0'*64,reviewer='human')]);r=mod.audit(self.root,self.manifest);self.assertEqual(r['categories']['betting_markets']['integrity_pass_rows'],0)
    def test_path_traversal_fails(self):
        self.rows([dict.fromkeys(mod.REQUIRED,'')|dict(category='player_opportunity',source_name='test',source_url='https://example.org',evidence_path='../outside',sha256='0'*64,reviewer='human')]);r=mod.audit(self.root,self.manifest);self.assertIn('relative within project',str(r['categories']['player_opportunity']['findings']))
if __name__=='__main__':unittest.main()
