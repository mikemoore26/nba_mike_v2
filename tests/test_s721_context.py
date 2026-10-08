import importlib.util
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_21/run_s7_21.py'
spec=importlib.util.spec_from_file_location('s721',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_provenance():
 assert m.PROV.fullmatch('EXPLICIT:p3:y132.84')
 assert not m.PROV.fullmatch('INHERITED:p3:y132.84')
def test_columns():
 assert m.FIELDS[-2:]==['verdict','detail']
