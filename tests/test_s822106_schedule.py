import csv, importlib.util, pathlib, tempfile, unittest
P=pathlib.Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_6/run_s8_22_10_6.py'
spec=importlib.util.spec_from_file_location('schedule_reconcile',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class TestSchedule(unittest.TestCase):
 def test_eight_games(self): self.assertEqual(sum(d=='2023-11-15' for d,x in m.SCHEDULE),8)
 def test_two_next_day(self): self.assertEqual(sum(d=='2023-11-16' for d,x in m.SCHEDULE),2)
 def test_correct(self): self.assertEqual(m.classify('2023-11-15','MIN@PHX'),'CORROBORATED_ORIENTATION')
 def test_reversed(self): self.assertEqual(m.classify('2023-11-15','PHX@MIN'),'REVERSED_VS_EXTERNAL_SCHEDULE')
 def test_date_aware(self): self.assertEqual(m.classify('2023-11-15','BKN@MIA'),'NOT_IN_EXTERNAL_SCHEDULE_SCOPE')
 def test_missing(self): self.assertEqual(m.classify('','BOS@PHI'),'MISSING_DATE_OR_MATCHUP')
 def test_end_to_end(self):
  with tempfile.TemporaryDirectory() as t:
   root=pathlib.Path(t);ledger=root/'ledger.csv';out=root/'out'
   with ledger.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['record_id','game_date_candidate','matchup_candidate','manual_decision']);w.writeheader();w.writerow(dict(record_id='P-001',game_date_candidate='2023-11-15',matchup_candidate='BOS@PHI',manual_decision='PENDING'))
   r=m.run(root,ledger,out);self.assertEqual(r['record_count'],1);self.assertEqual(r['decision'],'BLOCK_TRAINING');self.assertTrue((out/'unique_matchup_reconciliation.csv').exists())
if __name__=='__main__':unittest.main()
