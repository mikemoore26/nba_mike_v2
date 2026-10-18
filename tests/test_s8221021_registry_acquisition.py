import importlib.util,json,sys
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_21/run_s8_22_10_21.py'
spec=importlib.util.spec_from_file_location('acquire21',P);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
def fixture(rows):
    return json.dumps({'resultSets':[{'name':'CommonAllPlayers','headers':['PERSON_ID','DISPLAY_FIRST_LAST','TEAM_ABBREVIATION'],'rowSet':rows}]}).encode()
def test_url():
    assert m.url().startswith('https://stats.nba.com/stats/commonallplayers?')
    assert 'Season=2023-24' in m.url()
def test_sha():assert m.sha(b'abc')=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
def test_valid(monkeypatch,tmp_path):
    parent=tmp_path/'research/p0_s8/s8_22_10_20';parent.mkdir(parents=True)
    import zipfile
    # This test uses the real adjacent milestone module when running in the repository.
    actual=P.parents[1]/'s8_22_10_20/run_s8_22_10_20.py'
    assert actual.is_file()
    assert m.validate(fixture([[123,'Jane Doe','NYK']]))==(1,1)
def test_duplicate_same_id():assert m.validate(fixture([[123,'Jane Doe','NYK'],[123,'Jane Doe','BOS']]))==(2,1)
def test_duplicate_conflicting_id():
    with pytest.raises(ValueError,match='Conflicting'):m.validate(fixture([[123,'Jane Doe','NYK'],[123,'Other Name','BOS']]))
@pytest.mark.parametrize('payload',[b'',b'{}',b'not-json',b'{"resultSets":[]}'])
def test_invalid(payload):
    with pytest.raises((ValueError,json.JSONDecodeError)):m.validate(payload)
def test_fixture_capture(tmp_path):
    f=tmp_path/'fixture.json';f.write_bytes(fixture([[123,'Jane Doe','NYK']]))
    result=m.run(tmp_path,fixture=f)
    assert result['mode']=='OFFLINE_FIXTURE_UNVERIFIED'
    assert result['training_decision']=='BLOCK_TRAINING'
    assert result['historical_team_membership_certified'] is False
    raw=tmp_path/'research/p0_s8/s8_22_10_21/results/2023-24'/result['raw_sha256'][:16]/'commonallplayers_raw.json'
    assert raw.read_bytes()==f.read_bytes()
def test_capture_repeated(tmp_path):
    f=tmp_path/'fixture.json';f.write_bytes(fixture([[123,'Jane Doe','NYK']]))
    assert m.run(tmp_path,fixture=f)['raw_sha256']==m.run(tmp_path,fixture=f)['raw_sha256']
def test_invalid_fixture_no_capture(tmp_path):
    f=tmp_path/'fixture.json';f.write_text('{}')
    with pytest.raises(ValueError):m.run(tmp_path,fixture=f)
    assert not list(tmp_path.rglob('capture_manifest.json'))
