import hashlib
import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
m=load(ROOT/'research/p0_s8/s8_22_10_13/run_s8_22_10_13.py','s813')
prior=load(ROOT/'tests/test_s8221012_certification.py','prior_tests')

def setup(tmp_path,tamper=False):
    fx=prior.fixture(tmp_path,tamper)
    dst=tmp_path/'research/p0_s8/s8_22_10_12/run_s8_22_10_12.py'
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_bytes((ROOT/'research/p0_s8/s8_22_10_12/run_s8_22_10_12.py').read_bytes())
    cw=fx[1];digest=hashlib.sha256(cw.read_bytes()).hexdigest()
    target=tmp_path/'research/p0_s8/s8_22_10_7/results/2023-11-15/9194687df27944ca/provisional_game_id_crosswalk.csv'
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(cw.read_bytes())
    return fx,target,digest

def test_crosswalk_discovery_different_folder(tmp_path):
    _,target,digest=setup(tmp_path)
    assert m.verified_crosswalk(tmp_path,digest)==target

def test_all_eight_automated_not_human(tmp_path):
    fx,_,digest=setup(tmp_path)
    rows,_=m.verify(tmp_path,schedule_csv=fx[2],page_csv=fx[3],expected_sha=digest)
    assert len(rows)==8
    assert all(r['verification_status']=='AUTOMATED_VERIFIED' for r in rows)
    assert all(r['crosswalk_sha256']==digest for r in rows)

def test_tampered_page_goes_to_exception(tmp_path):
    fx,_,digest=setup(tmp_path,True)
    rows,_=m.verify(tmp_path,schedule_csv=fx[2],page_csv=fx[3],expected_sha=digest)
    assert sum(r['verification_status']=='MANUAL_EXCEPTION_REQUIRED' for r in rows)==1

def test_wrong_crosswalk_digest_fails_closed(tmp_path):
    fx,_,digest=setup(tmp_path)
    with pytest.raises(ValueError,match='Crosswalk SHA256 mismatch'):
        m.verify(tmp_path,crosswalk=fx[1],schedule_csv=fx[2],page_csv=fx[3],expected_sha='0'*64)

def test_missing_crosswalk_fails_closed(tmp_path):
    setup(tmp_path)
    with pytest.raises(ValueError,match='Expected one exact-SHA256 crosswalk'):
        m.verified_crosswalk(tmp_path,'0'*64)

def test_duplicate_matching_crosswalk_fails_closed(tmp_path):
    _,target,digest=setup(tmp_path)
    other=target.parent.parent/'another/provisional_game_id_crosswalk.csv'
    other.parent.mkdir();other.write_bytes(target.read_bytes())
    with pytest.raises(ValueError,match='found 2 matches'):
        m.verified_crosswalk(tmp_path,digest)

def test_schedule_tampering_blocks_all(tmp_path):
    fx,_,digest=setup(tmp_path)
    fx[4].write_bytes(b'tampered')
    rows,_=m.verify(tmp_path,schedule_csv=fx[2],page_csv=fx[3],expected_sha=digest)
    assert all(r['verification_status']=='MANUAL_EXCEPTION_REQUIRED' for r in rows)
