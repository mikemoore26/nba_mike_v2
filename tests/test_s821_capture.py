import hashlib
import importlib.util
from pathlib import Path
import sqlite3
import pytest

P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_21/run_s8_21.py'
spec=importlib.util.spec_from_file_location('s821',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def add(root,payload=b'demo',**kw):
    return m.capture(root,kind='schedule',url='fixture://schedule',checkpoint='T-24H',payload=payload,**kw)

def test_capture_integrity(tmp_path):
    e=add(tmp_path)
    assert e['outcome']=='SUCCESS'
    assert (tmp_path/e['blob_path']).read_bytes()==b'demo'
    assert m.integrity(tmp_path)['corrupt_or_missing']==[]

def test_duplicate_appends_not_overwrites(tmp_path):
    a=add(tmp_path);b=add(tmp_path)
    assert b['outcome']=='DUPLICATE'
    with sqlite3.connect(tmp_path/'capture_ledger.sqlite3') as c:
        assert c.execute('select count(*) from capture_events').fetchone()[0]==2
        assert c.execute('select duplicate_of from capture_events order by rowid desc limit 1').fetchone()[0]==a['event_id']

def test_failure_is_recorded(tmp_path):
    e=add(tmp_path,payload=None,error_code='TIMEOUT')
    assert e['outcome']=='FAILURE'
    assert m.report(tmp_path)['outcomes']['FAILURE']==1

def test_corruption_is_detected(tmp_path):
    e=add(tmp_path)
    (tmp_path/e['blob_path']).write_bytes(b'tampered')
    assert m.integrity(tmp_path)['corrupt_or_missing']
    with pytest.raises(ValueError,match='integrity'):add(tmp_path)

def test_invalid_inputs_fail_closed(tmp_path):
    with pytest.raises(ValueError):m.capture(tmp_path,kind='unknown',url='fixture://x',checkpoint='T-24H',payload=b'a')
    with pytest.raises(ValueError):m.capture(tmp_path,kind='schedule',url='http://x',checkpoint='T-24H',payload=b'a')
    with pytest.raises(ValueError):m.capture(tmp_path,kind='schedule',url='fixture://x',checkpoint='T-1M',payload=b'a')
    with pytest.raises(ValueError):add(tmp_path,payload=None)

def test_demo_health(tmp_path):
    m.demo(tmp_path);r=m.report(tmp_path)
    assert r['outcomes']=={'SUCCESS':2,'DUPLICATE':1,'FAILURE':1}
    assert r['decision']=='BLOCK_TRAINING' and r['network_requests']==0
    assert 'T-30M' in r['checkpoints_missing']

def test_no_training_or_live_network(tmp_path):
    source=P.read_text()
    assert 'import urllib' not in source and 'import requests' not in source
    assert 'model_fits' in source
