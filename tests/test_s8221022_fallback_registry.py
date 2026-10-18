import importlib.util
import json
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_22/run_s8_22_10_22.py'
spec=importlib.util.spec_from_file_location('s8221022',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def payload(rows):return json.dumps(rows).encode()

def test_validate():assert m.validate(payload([{'id':1,'full_name':'Jane Doe'}]))==[(1,'Jane Doe')]
@pytest.mark.parametrize('rows',[[],{},[{}],[{'id':'1','full_name':'A'}],[{'id':0,'full_name':'A'}],[{'id':True,'full_name':'A'}],[{'id':1,'full_name':''}],[{'id':1,'full_name':'A'},{'id':1,'full_name':'B'}]])
def test_bad(rows):
    with pytest.raises(ValueError):m.validate(payload(rows))
def test_invalid_json():
    with pytest.raises(json.JSONDecodeError):m.validate(b'no')
def test_offline_capture(tmp_path):
    src=tmp_path/'input.json';src.write_bytes(payload([{'id':1,'full_name':'Jane Doe'},{'id':2,'full_name':'John Roe'}]))
    out=m.run(tmp_path,offline=src)
    assert out['players_count']==2 and out['player_ids_certified']==0
    folder=tmp_path/'research/p0_s8/s8_22_10_22/results/2023-11-15'/out['raw_sha256'][:16]
    bridge=json.loads((folder/'third_party_name_only_registry_adapter.json').read_text())
    assert bridge['resultSets'][0]['rowSet']==[[1,'Jane Doe',''],[2,'John Roe','']]
    assert out['training_decision']=='BLOCK_TRAINING'
def test_repeat(tmp_path):
    src=tmp_path/'input.json';src.write_bytes(payload([{'id':1,'full_name':'Jane Doe'}]))
    a=m.run(tmp_path,offline=src);b=m.run(tmp_path,offline=src)
    assert a['raw_sha256']==b['raw_sha256']
def test_invalid_no_capture(tmp_path):
    src=tmp_path/'input.json';src.write_text('{}')
    with pytest.raises(ValueError):m.run(tmp_path,offline=src)
    assert not list(tmp_path.rglob('capture_manifest.json'))
def test_no_unexpected_redirect(monkeypatch):
    class R:
        status=200;headers={}
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def geturl(self):return 'https://example.com/players.json'
    monkeypatch.setattr(m.urllib.request,'urlopen',lambda *args,**kwargs:R())
    with pytest.raises(ValueError,match='redirect'):m.fetch(2)
