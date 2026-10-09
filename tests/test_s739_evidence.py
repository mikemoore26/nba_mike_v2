import csv,hashlib,importlib.util,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_39/run_s7_39.py'
spec=importlib.util.spec_from_file_location('s739',P);s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
class TestS739(unittest.TestCase):
 def test_normalize_accents(self):self.assertEqual(s.norm('Porziņģis'), 'porzingis')
 def test_name_boundary(self):self.assertFalse(s.has_name('Annette traded','Ann'))
 def test_name_positive(self):self.assertTrue(s.has_name('Kristaps Porzingis traded','Kristaps Porziņģis'))
 def test_transaction(self):self.assertTrue(s.TRANSACTION.search('traded'))
 def test_team_mentions(self):self.assertEqual(s.teams_in('Hawks sent him to Warriors'),['ATL','GSW'])
 def test_no_team(self):self.assertEqual(s.teams_in('Anthony Davis traded'),[])
 def test_script_excluded(self):self.assertFalse(any('Anthony Davis' in x for x in s.statements(b'<html><script>Anthony Davis traded</script><p>Hello.</p></html>')))
 def fixture(self,t,raw):
  sha=hashlib.sha256(raw).hexdigest();obj=t/'objects';obj.mkdir();(obj/(sha+'.html')).write_bytes(raw)
  row=dict.fromkeys(s.FIELDS,'');row.update(candidate_number='7',player_name='Anthony Davis',player_id='123',event_date='2026-02-05',to_team='WAS',article_url='https://www.nba.com/news/x',capture_status='CAPTURED',relevance_status='RELEVANT_REVIEW_ONLY',article_sha256=sha,article_bytes=str(len(raw)),historical_publication_verified='false',origin_team_verified='false')
  src=t/'review.csv'
  with src.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=s.FIELDS);w.writeheader();w.writerow(row)
  return src,obj
 def test_end_to_end(self):
  with tempfile.TemporaryDirectory() as tmp:
   t=Path(tmp);src,obj=self.fixture(t,b'<html><p>Anthony Davis was traded from the Mavericks to the Wizards.</p></html>')
   r=s.run(src,obj,t/'out');self.assertEqual(r['same_sentence_review_rows'],1);self.assertEqual(r['origin_teams_verified'],0)
   with (t/'out/s7_39_review.csv').open() as f:row=list(csv.DictReader(f))[0]
   self.assertEqual(row['team_mentions'],'DAL;WAS');self.assertEqual(row['origin_team_verified'],'false')
 def test_separate_sentence_no_match(self):
  with tempfile.TemporaryDirectory() as tmp:
   t=Path(tmp);src,obj=self.fixture(t,b'<html><p>Anthony Davis is a player. The team traded another player.</p></html>')
   r=s.run(src,obj,t/'out');self.assertEqual(r['same_sentence_review_rows'],0)
 def test_hash_tampering(self):
  with tempfile.TemporaryDirectory() as tmp:
   t=Path(tmp);src,obj=self.fixture(t,b'<html><p>Anthony Davis traded.</p></html>');next(obj.iterdir()).write_bytes(b'bad')
   with self.assertRaisesRegex(ValueError,'SHA mismatch'):s.run(src,obj,t/'out')
 def test_missing_object(self):
  with tempfile.TemporaryDirectory() as tmp:
   t=Path(tmp);src,obj=self.fixture(t,b'<html><p>Anthony Davis traded.</p></html>');next(obj.iterdir()).unlink()
   with self.assertRaisesRegex(ValueError,'Missing captured'):s.run(src,obj,t/'out')
 def test_invalid_schema(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'x.csv';p.write_text('bad\n1\n')
   with self.assertRaisesRegex(ValueError,'schema'):s.load(p)
 def test_no_promoted_flag(self):
  with tempfile.TemporaryDirectory() as tmp:
   t=Path(tmp);src,obj=self.fixture(t,b'<html><p>Anthony Davis traded.</p></html>');text=src.read_text().replace(',false,false',',true,false');src.write_text(text)
   with self.assertRaises(ValueError):s.load(src)
if __name__=='__main__':unittest.main()
