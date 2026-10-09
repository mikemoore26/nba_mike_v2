import importlib.util
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_20/run_s8_20.py'
spec=importlib.util.spec_from_file_location('s820',SCRIPT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_recommended_hybrid(): assert m.STRATEGIES[-1][0]=='hybrid'
def test_historical_research_only(): assert m.STRATEGIES[0][-1]=='DO_NOT_PROMOTE'
def test_future_checkpoints_before_tipoff(): assert all(minutes<0 for _,minutes in m.CHECKPOINTS)
def test_no_duplicate_sources(): assert len({s[0] for s in m.SOURCES})==len(m.SOURCES)
def test_no_prior_reports(tmp_path):
    result=m.run(tmp_path)
    assert result['decision']=='BLOCK_TRAINING'
    assert result['prospective_snapshots_collected']==0
    assert result['network_requests']==0
    assert all(not row['exists'] for row in result['prior_reports'])
def test_existing_prior_report_not_certified(tmp_path):
    p=tmp_path/'research/p0_s8/s8_19/results/s8_19_report.json'
    p.parent.mkdir(parents=True)
    p.write_text('{"decision":"ALLOW_TRAINING"}')
    result=m.run(tmp_path)
    assert result['decision']=='BLOCK_TRAINING'
    assert result['prior_reports'][-1]['reported_decision']=='ALLOW_TRAINING'
    assert result['training_eligible'] is False
def test_outputs(tmp_path):
    m.run(tmp_path)
    out=tmp_path/'research/p0_s8/s8_20/results'
    assert len(list(out.glob('s8_20_*')))==5
