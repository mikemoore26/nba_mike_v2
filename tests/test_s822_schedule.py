import importlib.util
import json
from pathlib import Path
import pytest

SRC=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22/run_s8_22.py'
spec=importlib.util.spec_from_file_location('s822',SRC)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

@pytest.fixture
def root(tmp_path):
    source=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_21/run_s8_21.py'
    target=tmp_path/'research/p0_s8/s8_21/run_s8_21.py'
    target.parent.mkdir(parents=True)
    target.write_bytes(source.read_bytes())
    return tmp_path

def valid():
    return json.loads((SRC.parent/'fixture_schedule.json').read_text())

def parse(obj): return m.parse_schedule(json.dumps(obj).encode())

def test_valid():
    rows=parse(valid());assert len(rows)==1 and rows[0]['home_team']=='NYK'

def test_invalid_json():
    with pytest.raises(ValueError,match='INVALID_JSON'):m.parse_schedule(b'bad')

def test_schema_missing():
    with pytest.raises(ValueError,match='MISSING_LEAGUE_SCHEDULE'):parse({})

def test_missing_id():
    d=valid();d['leagueSchedule']['gameDates'][0]['games'][0]['gameId']='x'
    with pytest.raises(ValueError,match='INVALID_GAME_ID'):parse(d)

def test_duplicate_id():
    d=valid();g=d['leagueSchedule']['gameDates'][0]['games'][0];d['leagueSchedule']['gameDates'][0]['games'].append(g)
    with pytest.raises(ValueError,match='DUPLICATE_GAME_ID'):parse(d)

def test_bad_timezone():
    d=valid();d['leagueSchedule']['gameDates'][0]['games'][0]['gameDateTimeUTC']='2026-10-10T23:30:00'
    with pytest.raises(ValueError,match='NON_UTC_TIPOFF'):parse(d)

def test_bad_team():
    d=valid();d['leagueSchedule']['gameDates'][0]['games'][0]['awayTeam']['teamTricode']='NYK'
    with pytest.raises(ValueError,match='INVALID_TEAM_TRICODE'):parse(d)

def test_fixture_capture(root):
    r=m.run(root,fixture=SRC.parent/'fixture_schedule.json')
    assert r['parse_status']=='PASS' and r['parsed_game_count']==1 and r['capture_outcome']=='SUCCESS'
    assert r['decision']=='BLOCK_TRAINING'
    r2=m.run(root,fixture=SRC.parent/'fixture_schedule.json')
    assert r2['capture_outcome']=='DUPLICATE'
    assert len(list((root/'research/p0_s8/s8_22/results').glob('s8_22_receipt_*.json')))==2

def test_bad_schema_still_preserved(root,tmp_path):
    bad=tmp_path/'bad.json';bad.write_text('{}')
    r=m.run(root,fixture=bad)
    assert r['parse_status']=='MISSING_LEAGUE_SCHEDULE' and r['sha256']

def test_missing_fixture_logged(root,tmp_path):
    r=m.run(root,fixture=tmp_path/'absent.json')
    assert r['capture_outcome']=='FAILURE' and r['retrieval_error']=='FIXTURE_READ_FAILED_FileNotFoundError'

def test_live_fake_fetcher(root):
    raw=(SRC.parent/'fixture_schedule.json').read_bytes()
    r=m.run(root,live=True,fetcher=lambda url:(200,{'date':'fake'},raw))
    assert r['mode']=='LIVE_MANUAL' and r['response_headers']=={'date':'fake'}

def test_live_error_logged(root):
    def boom(url):raise OSError('offline')
    r=m.run(root,live=True,fetcher=boom)
    assert r['capture_outcome']=='FAILURE' and r['parse_status']=='NOT_ATTEMPTED'

def test_live_url_restriction():
    with pytest.raises(ValueError,match='UNAPPROVED_SOURCE_URL'):m.fetch_live('https://example.com')

def test_ambiguous_modes(root):
    with pytest.raises(ValueError,match='exactly one'):m.run(root)
