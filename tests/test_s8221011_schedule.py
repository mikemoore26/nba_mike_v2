import importlib.util
from pathlib import Path
import tempfile
import unittest

SRC=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_11/run_s8_22_10_11.py'
spec=importlib.util.spec_from_file_location('s8221011',SRC);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_anchor_discovery(self):
  d,c=m.discover(b'<a href="/game/dal-vs-was-0022300192">Game</a>');self.assertEqual(d['DAL@WAS'],'0022300192');self.assertFalse(c)
 def test_script_id_ignored(self):
  d,c=m.discover(b'<script>"/game/dal-vs-was-0022300192"</script>');self.assertEqual(d,{})
 def test_conflicts(self):
  d,c=m.discover(b'<a href="/game/dal-vs-was-0022300192"></a><a href="/game/dal-vs-was-0022300193"></a>');self.assertIn('DAL@WAS',c);self.assertNotIn('DAL@WAS',d)
 def test_not_a_game(self):
  d,c=m.discover(b'<a href="/game/dal-vs-was-123"></a>');self.assertEqual(d,{})
 def test_reconcile_no_auto_certification(self):
  cw=[{'game_date':m.DATE,'away_at_home':a,'game_id_status':'UNVERIFIED_PROVISIONAL','provisional_nba_game_id':f'002230019{i}'} for i,a in enumerate(['DAL@WAS','NYK@ATL','BOS@PHI','MIL@TOR','ORL@CHI','MIN@PHX','SAC@LAL','CLE@POR'],2)]
  pages=[{'away_at_home':r['away_at_home'],'content_status':'TITLE_MATCH_REVIEW_REQUIRED','snapshot_sha256':'abc'} for r in cw]
  out=m.reconcile(cw,{r['away_at_home']:r['provisional_nba_game_id'] for r in cw},set(),pages,'def')
  self.assertEqual(len(out),8);self.assertTrue(all(r['evidence_status']=='CANDIDATE_REVIEW_REQUIRED' and r['review_decision']=='PENDING' for r in out))
 def test_mismatch_blocks(self):
  cw=[{'game_date':m.DATE,'away_at_home':a,'game_id_status':'UNVERIFIED_PROVISIONAL','provisional_nba_game_id':f'002230019{i}'} for i,a in enumerate(['DAL@WAS','NYK@ATL','BOS@PHI','MIL@TOR','ORL@CHI','MIN@PHX','SAC@LAL','CLE@POR'],2)]
  out=m.reconcile(cw,{'DAL@WAS':'0022300999'},set(),[],'')
  self.assertEqual(next(r for r in out if r['away_at_home']=='DAL@WAS')['discovery_status'],'ID_MISMATCH')
 def test_missing_snapshot_offline(self):
  with tempfile.TemporaryDirectory() as d:
   data,status,error=m.snapshot(Path(d)/'x.html',m.SCHEDULE_URL,1,True);self.assertIsNone(data);self.assertEqual(status,'OFFLINE_NO_SNAPSHOT')
 def test_snapshot_immutable(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x.html';url=m.SCHEDULE_URL
   data,status,_=m.snapshot(p,url,1,False,lambda u,t:b'<html>first</html>')
   data2,status2,_=m.snapshot(p,url,1,False,lambda u,t:b'<html>second</html>')
   self.assertEqual(data,data2);self.assertEqual(status2,'REUSED_EXISTING_SNAPSHOT')
 def test_receipt_tamper_detection(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x.html';m.snapshot(p,m.SCHEDULE_URL,1,False,lambda u,t:b'original');p.write_bytes(b'tampered')
   with self.assertRaises(ValueError):m.snapshot(p,m.SCHEDULE_URL,1,True)
if __name__=='__main__':unittest.main()
