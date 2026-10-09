import importlib.util
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
import io
import pytest

P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_4/run_s8_22_4.py'
spec=importlib.util.spec_from_file_location('s8224',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def fixture(**kw):
    return json.dumps({'data':[{'id':10,'date':'2026-10-10','datetime':'2026-10-10T23:30:00Z',
            'home_team':{'id':1},'visitor_team':{'id':2},'status':'scheduled'}],
            'meta':{'next_cursor':None},**kw}).encode()

def test_valid():
    a=m.parse_games(fixture(),'2026-10-10');assert len(a)==1 and a[0]['official_nba_game_id']==''
    assert a[0]['tipoff_utc'].startswith('2026-10-10T23:30')
def test_missing_time():
    x=json.loads(fixture());x['data'][0].pop('datetime');a=m.parse_games(json.dumps(x).encode(),'2026-10-10');assert a[0]['tipoff_status']=='MISSING'
def test_no_invented_time():
    x=json.loads(fixture());x['data'][0]['datetime']='2026-10-10';a=m.parse_games(json.dumps(x).encode(),'2026-10-10');assert a[0]['tipoff_utc']==''
def test_bad_json():
    with pytest.raises(ValueError,match='INVALID_JSON'):m.parse_games(b'no','2026-10-10')
def test_bad_envelope():
    with pytest.raises(ValueError,match='INVALID_ENVELOPE'):m.parse_games(b'{}','2026-10-10')
def test_pagination():
    with pytest.raises(ValueError,match='PAGINATION_INCOMPLETE'):m.parse_games(fixture(meta={'next_cursor':23}),'2026-10-10')
def test_bad_id():
    x=json.loads(fixture());x['data'][0]['id']=None
    with pytest.raises(ValueError,match='INVALID_OR_DUPLICATE_GAME_ID'):m.parse_games(json.dumps(x).encode(),'2026-10-10')
def test_date_mismatch():
    with pytest.raises(ValueError,match='DATE_MISMATCH'):m.parse_games(fixture(),'2026-10-11')
def test_bad_team():
    x=json.loads(fixture());x['data'][0]['visitor_team']['id']=1
    with pytest.raises(ValueError,match='INVALID_TEAMS'):m.parse_games(json.dumps(x).encode(),'2026-10-10')
def test_missing_key(tmp_path,monkeypatch):
    monkeypatch.delenv('BALLDONTLIE_API_KEY',raising=False)
    with pytest.raises(RuntimeError,match='missing'):m.load_key(tmp_path)
def test_bad_date(tmp_path):
    with pytest.raises(ValueError,match='YYYY-MM-DD'):m.run(tmp_path,game_date='2026/10/10',fixture=P)
def test_http_403():
    def op(req,timeout):raise HTTPError(req.full_url,403,'Forbidden',{},io.BytesIO(b'private'))
    body,status,err,url,headers=m.fetch('secret','2026-10-10',op)
    assert body is None and status==403 and err=='HTTP_403' and 'secret' not in url
def test_network_error():
    def op(req,timeout):raise URLError('no route')
    assert m.fetch('secret','2026-10-10',op)[2]=='NETWORK_URLError'
def test_live_request_headers():
    class Resp:
        headers={'Content-Type':'application/json'}
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def getcode(self):return 200
        def read(self,n):return fixture()
    def op(req,timeout):
        assert req.get_header('Authorization')=='secret';assert 'secret' not in req.full_url
        return Resp()
    assert m.fetch('secret','2026-10-10',op)[1]==200

def test_fixture_integration(tmp_path):
    # Install S8.21 dependency into an isolated project root.
    import zipfile
    z=Path('/mnt/data/nba_mike_v2_S8_21_patch.zip')
    if not z.exists():pytest.skip('S8.21 ZIP unavailable')
    with zipfile.ZipFile(z) as f:
        target=tmp_path/'research/p0_s8/s8_21/run_s8_21.py';target.parent.mkdir(parents=True)
        target.write_bytes(f.read('research/p0_s8/s8_21/run_s8_21.py'))
    fixture_path=tmp_path/'fixture.json';fixture_path.write_bytes(fixture())
    result=m.run(tmp_path,game_date='2026-10-10',fixture=fixture_path)
    assert result['parsed_games']==1 and result['decision']=='BLOCK_TRAINING'
    assert (tmp_path/'research/p0_s8/s8_21/artifacts/capture_ledger.sqlite3').exists()
    assert result['raw_sha256']
