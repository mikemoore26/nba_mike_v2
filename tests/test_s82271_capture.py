import csv,importlib.util,json,shutil
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'research/p0_s8/s8_22_7_1/run_s8_22_7_1.py'
spec=importlib.util.spec_from_file_location('s82271',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def sandbox(tmp_path):
    for name in ['s8_22_4/run_s8_22_4.py','s8_22_4/fixture_games.json','s8_21/run_s8_21.py','s8_22_7/date_manifest.csv']:
        src=ROOT/'research/p0_s8'/name
        dst=tmp_path/'research/p0_s8'/name;dst.parent.mkdir(parents=True,exist_ok=True)
        if not src.is_file():pytest.skip('S8.21 missing from checkout')
        shutil.copy2(src,dst)
    return tmp_path

def test_bad_date(tmp_path):
    with pytest.raises(ValueError):m.run(tmp_path,'2023-99-99',fixture=Path('none'))

def test_mode_required(tmp_path):
    with pytest.raises(ValueError):m.run(tmp_path,'2023-10-24')

def test_fixture_missing(tmp_path):
    with pytest.raises(ValueError):m.run(tmp_path,'2023-10-24',fixture=tmp_path/'missing')

def test_manifest_never_overwrites(tmp_path):
    root=tmp_path;f=root/'research/p0_s8/s8_22_7/date_manifest.csv';f.parent.mkdir(parents=True)
    f.write_text('date,phase,provider_csv,reference_csv,selection_reason\n2023-10-24,regular,old.csv,,test\n')
    p=root/'capture.csv';p.write_text('x')
    assert m.update_manifest(root,'2023-10-24',p)=='EXISTING_MANIFEST_VALUE_PRESERVED'
    assert 'old.csv' in f.read_text()

def test_manifest_updates_blank(tmp_path):
    root=tmp_path;f=root/'research/p0_s8/s8_22_7/date_manifest.csv';f.parent.mkdir(parents=True)
    f.write_text('date,phase,provider_csv,reference_csv,selection_reason\n2023-11-15,regular,,,test\n')
    p=root/'research/p0_s8/s8_22_7_1/captures/a.csv';p.parent.mkdir(parents=True);p.write_text('x')
    assert m.update_manifest(root,'2023-11-15',p)=='UPDATED'
    assert 'captures/a.csv' in f.read_text()
    assert (f.parent/(f.name+'.pre_s82271.bak')).exists()

def test_manifest_rejects_duplicate(tmp_path):
    f=tmp_path/'research/p0_s8/s8_22_7/date_manifest.csv';f.parent.mkdir(parents=True)
    f.write_text('date,phase,provider_csv,reference_csv,selection_reason\n2023-11-15,x,,,x\n2023-11-15,x,,,x\n')
    p=tmp_path/'test.csv';p.write_text('x')
    assert m.update_manifest(tmp_path,'2023-11-15',p)=='DATE_NOT_UNIQUE_IN_MANIFEST'

def test_hash():assert m.sha(b'abc')=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'

def test_manifest_missing(tmp_path):
    p=tmp_path/'x.csv';p.write_text('x')
    assert m.update_manifest(tmp_path,'2023-11-15',p)=='MANIFEST_MISSING'

def test_manifest_unknown_date(tmp_path):
    f=tmp_path/'research/p0_s8/s8_22_7/date_manifest.csv';f.parent.mkdir(parents=True)
    f.write_text('date,phase,provider_csv,reference_csv,selection_reason\n2023-11-15,x,,,x\n')
    p=tmp_path/'x.csv';p.write_text('x')
    assert m.update_manifest(tmp_path,'2024-01-15',p)=='DATE_NOT_UNIQUE_IN_MANIFEST'


def test_immutable_fixture_capture(tmp_path):
    root=sandbox(tmp_path)
    fixture=root/'research/p0_s8/s8_22_4/fixture_games.json'
    first,p1=m.run(root,'2026-10-10',fixture=fixture,update=True)
    second,p2=m.run(root,'2026-10-10',fixture=fixture,update=True)
    assert first['schedule_state']=='PROVIDER_GAMES_PRESENT_UNVERIFIED'
    assert first['manifest_status']=='UPDATED'
    assert second['manifest_status']=='EXISTING_PROVIDER_SNAPSHOT_PRESERVED'
    assert p1!=p2 and (p1/'provider_games.csv').exists() and (p2/'provider_games.csv').exists()
    assert first['decision']=='BLOCK_TRAINING'

def test_empty_schedule_not_verified(tmp_path):
    root=sandbox(tmp_path)
    fixture=tmp_path/'empty.json';fixture.write_text('{"data":[],"meta":{"next_cursor":null}}')
    report,_=m.run(root,'2023-11-15',fixture=fixture)
    assert report['schedule_state']=='EMPTY_SCHEDULE_UNVERIFIED'
    assert report['provider_rows']==0
