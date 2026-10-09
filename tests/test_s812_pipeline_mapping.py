from pathlib import Path
import importlib.util

SCRIPT=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_12/run_s8_12.py'
spec=importlib.util.spec_from_file_location('s812',SCRIPT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def fixture(tmp_path):
 root=tmp_path
 for folder in ('src/nba_mike','research/p0_s4/s4','research/p0_s4/s5','research/p0_s4/s5_1','research/p0_s4/s6'):
  (root/folder).mkdir(parents=True,exist_ok=True)
 for rel in m.PRIORITY:
  (root/rel).write_text('def main():\n    frame = make_form_frame(fetch())\n    score = frame.mean()\n    return score\n',encoding='utf-8')
 return root

def test_map_source_and_local_assignment(tmp_path):
 root=fixture(tmp_path);report,calls,edges,paths=m.run(root)
 assert report['issues']==[]
 assert report['training_eligible'] is False and report['decision']=='BLOCK_TRAINING'
 assert len(paths)==5
 assert any(e['assigned']=='frame' and 'make_form_frame' in e['calls'] for e in edges)
 assert all(p['conclusion']=='CALL_SITE_ONLY_NO_INTERPROCEDURAL_PROOF' for p in paths)

def test_fit_is_candidate_not_proof(tmp_path):
 root=fixture(tmp_path)
 path=root/m.PRIORITY[0];path.write_text('def main(x):\n    x.fit()\n    return x\n',encoding='utf-8')
 report,calls,_,_=m.run(root)
 assert report['fit_or_train_call_candidates']==1
 assert any(c['category']=='FIT_OR_TRAIN' and c['classification']=='SOURCE_CALL_ONLY' for c in calls)

def test_missing_priority_fails_closed(tmp_path):
 root=fixture(tmp_path);(root/m.PRIORITY[0]).unlink()
 report,*_=m.run(root)
 assert any(x.startswith('MISSING_PRIORITY:') for x in report['issues'])
 assert report['training_eligible'] is False

def test_syntax_failure_reported(tmp_path):
 root=fixture(tmp_path);(root/m.PRIORITY[0]).write_text('def broken(:\n',encoding='utf-8')
 report,*_=m.run(root)
 assert any(x.startswith('SCAN_ERROR:') for x in report['issues'])

def test_outputs_written(tmp_path):
 root=fixture(tmp_path);out=tmp_path/'output'
 assert m.main(['--project-root',str(root),'--output-dir',str(out)])==0
 assert (out/'s8_12_report.json').exists()
 assert (out/'s8_12_priority_paths.csv').exists()
 assert (out/'s8_12_assignment_edges.csv').exists()
