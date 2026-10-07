import importlib.util
from pathlib import Path
import pandas as pd

SCRIPT=Path(__file__).resolve().parents[1]/'research/p0_s4/s5_1/run_s5_1.py'
spec=importlib.util.spec_from_file_location('s51',SCRIPT)
s51=importlib.util.module_from_spec(spec)
spec.loader.exec_module(s51)

def frame():
    rows=[]
    for i in range(40):
        rows.append({'event_date':pd.Timestamp('2025-10-01')+pd.Timedelta(days=i),
                     'target_minutes':float(i%15+15),'last_5':20.0,'ewm_5':float(i%15+15)})
    return pd.DataFrame(rows)

def test_bootstrap_reproducible():
    assert s51.paired_bootstrap(frame(),iterations=80)==s51.paired_bootstrap(frame(),iterations=80)

def test_positive_gain_for_perfect_ewm():
    out=s51.paired_bootstrap(frame(),iterations=80)
    assert out['gain_minutes']>0 and out['mae_right']==0

def test_missing_data_excluded():
    x=frame();x.loc[0,'ewm_5']=float('nan')
    assert s51.paired_bootstrap(x,iterations=20)['n']==39

def test_snapshot_hash(tmp_path):
    p=tmp_path/'test.csv';p.write_text('a,b\n1,2\n')
    h=s51.sha(p)
    p.write_text('a,b\n1,3\n')
    assert h!=s51.sha(p)
