import csv
import importlib.util
from pathlib import Path
import pytest

RUNNER=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_7/run_s8_7.py'
spec=importlib.util.spec_from_file_location('s87',RUNNER)
s87=importlib.util.module_from_spec(spec);spec.loader.exec_module(s87)

def test_enclosing_function():
    t=__import__('ast').parse('def f():\n    x=1\n    return x\n')
    assert s87.enclosing_function(t,2).name=='f'

def test_trace_source():
    src='def f(df):\n    return df.shift(1)\n'
    finding={'line':'2','function':'f','rule':'ROLLING_OR_EXPANDING','severity':'MEDIUM'}
    r=s87.trace_source('x.py',src,[finding]);assert r['functions'][0]['name']=='f'
    assert 'shift(1)' in r['findings'][0]['excerpt']

def test_source_change_detection(tmp_path):
    project=tmp_path; rel='src/nba_mike/features/opportunity.py';p=project/rel;p.parent.mkdir(parents=True)
    p.write_text('def f():\n    return 1\n')
    f=tmp_path/'findings.csv'; i=tmp_path/'inventory.csv'
    with f.open('w',newline='') as o:
        w=csv.DictWriter(o,fieldnames=['path','line','function','rule','severity']);w.writeheader();w.writerow(dict(path=rel,line=2,function='f',rule='POSTGAME_FIELD',severity='MEDIUM'))
    with i.open('w',newline='') as o:
        w=csv.DictWriter(o,fieldnames=['path','sha256']);w.writeheader();w.writerow(dict(path=rel,sha256='old'))
    r=s87.audit(project,f,i,tmp_path/'out')
    assert r['decision']=='BLOCK_TRAINING'
    assert any(x['status']=='SOURCE_CHANGED' for x in r['issues'])
    assert (tmp_path/'out/s8_7_trace.csv').exists()

def test_missing_csv_does_not_authorize(tmp_path):
    r=s87.audit(tmp_path,tmp_path/'none',tmp_path/'none2',tmp_path/'out')
    assert not r['training_eligible']
    assert r['counts']['MISSING_SOURCE']==6
