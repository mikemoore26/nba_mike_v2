import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_7_4_1'))
from run_s8_22_7_4_1 import audit,archive,extract_visible

class TestAnnouncement(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        text='The 2023-24 NBA regular season will begin on Tuesday, Oct. 24 with doubleheader on TNT. Denver Nuggets will receive their championship rings before hosting the Los Angeles Lakers (7:30 p.m. ET). Phoenix Suns will visit the Golden State Warriors (10 p.m. ET).'
        data=('<html><body>'+text+'</body></html>').encode()
        rel='research/p0_s8/s8_22_7_2/evidence/2023-10-24/test/source.bin'
        p=self.root/rel;p.parent.mkdir(parents=True);p.write_bytes(data)
        self.receipt=p.parent/'receipt.json'
        self.receipt.write_text(json.dumps({'date':'2023-10-24','source_url':'https://www.nba.com/news/2023-24-nba-regular-season-schedule','retrieved_utc':'2026-10-10T00:21:01Z','sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'evidence_path':rel}))
        self.review=self.root/'review.csv';self.reference=self.root/'reference.csv'
        self.rows=[{'game_date':'2023-10-24','official_nba_game_id':'0022300061','home_team':'DEN','away_team':'LAL','tipoff_utc':'2023-10-24T23:30:00Z','matchup_quote':'Denver Nuggets will receive their championship rings before hosting the Los Angeles Lakers','tipoff_quote':'7:30 p.m. ET','date_coverage_quote':'The 2023-24 NBA regular season will begin on Tuesday, Oct. 24 with doubleheader on TNT'},
                   {'game_date':'2023-10-24','official_nba_game_id':'0022300062','home_team':'GSW','away_team':'PHX','tipoff_utc':'2023-10-25T02:00:00Z','matchup_quote':'Phoenix Suns will visit the Golden State Warriors','tipoff_quote':'10 p.m. ET','date_coverage_quote':'The 2023-24 NBA regular season will begin on Tuesday, Oct. 24 with doubleheader on TNT'}]
        self.save()
    def save(self):
        with self.review.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=self.rows[0].keys());w.writeheader();w.writerows(self.rows)
        with self.reference.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=('game_date','official_nba_game_id','home_team','away_team','tipoff_utc','source_url','evidence_sha256','evidence_retrieved_utc'))
            w.writeheader();w.writerows([{k:r.get(k,'') for k in w.fieldnames} for r in self.rows])
    def run_audit(self):return audit(self.root,'2023-10-24',self.receipt,self.review,self.reference)
    def test_agreement(self):self.assertTrue(self.run_audit()['row_set_agreement'])
    def test_still_not_certified(self):self.assertEqual(self.run_audit()['date_completeness'],'NOT_CERTIFIED')
    def test_training_blocked(self):self.assertFalse(self.run_audit()['training_eligible'])
    def test_report_written(self):self.assertTrue((self.root/self.run_audit()['report_path']).exists())
    def test_missing_quote(self):
        self.rows[0]['matchup_quote']='Lakers @ Nuggets game ID 0022300061';self.save()
        self.assertFalse(self.run_audit()['row_set_agreement'])
    def test_missing_coverage_quote(self):
        for row in self.rows:row['date_coverage_quote']=''
        self.save();self.assertFalse(self.run_audit()['coverage_quote_present'])
    def test_wrong_team(self):
        self.rows[0]['home_team']='NYK';self.save()
        with self.reference.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=('game_date','official_nba_game_id','home_team','away_team','tipoff_utc'));w.writeheader()
            w.writerow({'game_date':'2023-10-24','official_nba_game_id':'0022300061','home_team':'DEN','away_team':'LAL','tipoff_utc':'2023-10-24T23:30:00Z'})
            w.writerow({'game_date':'2023-10-24','official_nba_game_id':'0022300062','home_team':'GSW','away_team':'PHX','tipoff_utc':'2023-10-25T02:00:00Z'})
        self.assertTrue(self.run_audit()['conflicts'])
    def test_tampered_archive(self):
        (self.receipt.parent/'source.bin').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'INTEGRITY'):self.run_audit()
    def test_wrong_host(self):
        x=json.loads(self.receipt.read_text());x['source_url']='https://www.nba.com.evil.org/';self.receipt.write_text(json.dumps(x))
        with self.assertRaisesRegex(ValueError,'NON_OFFICIAL'):self.run_audit()
    def test_wrong_date(self):
        with self.assertRaisesRegex(ValueError,'DATE_MISMATCH'):audit(self.root,'2023-10-25',self.receipt,self.review,self.reference)
    def test_duplicate(self):
        self.rows.append(dict(self.rows[0]));self.save()
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):self.run_audit()
    def test_missing_reference_game(self):
        with self.reference.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=('game_date','official_nba_game_id','home_team','away_team','tipoff_utc'));w.writeheader();w.writerow({k:self.rows[0][k] for k in w.fieldnames})
        self.assertEqual(self.run_audit()['missing_in_game_reference'],['0022300062'])
    def test_no_game_id_required_in_announcement(self):
        visible=extract_visible((self.receipt.parent/'source.bin').read_bytes())
        self.assertNotIn('0022300061',visible)
        self.assertTrue(self.run_audit()['row_set_agreement'])
if __name__=='__main__':unittest.main()
