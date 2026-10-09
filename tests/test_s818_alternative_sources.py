import importlib.util
from pathlib import Path

P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_18/run_s8_18.py'
spec=importlib.util.spec_from_file_location('s818',P); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_sources_unique(): assert len({s[0] for s in m.SOURCES})==len(m.SOURCES)
def test_pre_tipoff_claim(): assert m.claimed_before('2023-10-24T18:30:00-04:00') is True
def test_post_tipoff_claim(): assert m.claimed_before('2023-10-24T19:31:00-04:00') is False
def test_date_only_unknown(): assert m.claimed_before('2023-10-24') is None
def test_offline_no_certification(tmp_path):
    r=m.audit(tmp_path);assert r['decision']=='BLOCK_TRAINING' and r['historical_captures_verified']==0
    assert (tmp_path/'research/p0_s8/s8_18/results/s8_18_source_audit.csv').exists()
def test_postgame_never_pregame(tmp_path):
    m.audit(tmp_path)
    import csv
    rows=list(csv.DictReader((tmp_path/'research/p0_s8/s8_18/results/s8_18_source_audit.csv').open()))
    assert next(x for x in rows if x['source_id']=='nba_postgame_box')['verdict']=='POST_TIPOFF_OUTCOME_ONLY'
