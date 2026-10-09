import importlib.util
from pathlib import Path
import pandas as pd

def load():
 p=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_11/run_s8_11.py'
 spec=importlib.util.spec_from_file_location('s811_runner',p)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def test_governance_constant():
 m=load();assert m.DENIED >= {'min','pts','target_minutes'}

def test_candidate_lists_exclude_outcomes():
 m=load();assert all(not (set(cols)&m.DENIED) for cols in m.CANDIDATES.values())

def test_ast_discovers_calls(tmp_path):
 m=load();p=tmp_path/'src/nba_mike';p.mkdir(parents=True)
 (p/'a.py').write_text('def foo(x):\n    x.fit()\n    x.predict()\n')
 q=tmp_path/'research/p0_s4';q.mkdir(parents=True)
 rows,count,issues=m.locate(tmp_path)
 assert count==1 and not issues and {r['call'] for r in rows}=={'fit','predict'}

def test_ast_bad_file_blocks(tmp_path):
 m=load();p=tmp_path/'src/nba_mike';p.mkdir(parents=True)
 (p/'broken.py').write_text('def foo(:\n')
 (tmp_path/'research/p0_s4').mkdir(parents=True)
 _,_,issues=m.locate(tmp_path);assert any('PARSE:' in e for e in issues)

def test_no_fit_in_exercise_source():
 import inspect
 m=load();source=inspect.getsource(m.exercise)
 assert '.fit(' not in source and '.fit_transform(' not in source
