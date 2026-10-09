import csv, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_2'))
from run_s8_22_2 import SOURCES, evaluate

def test_sources_unique(): assert len({s['source_id'] for s in SOURCES}) == len(SOURCES)
def test_nba_blocked(): assert next(s for s in SOURCES if s['source_id']=='NBA_CDN_S822')['recommendation'].startswith('BLOCKED')
def test_espn_unverified(): assert next(s for s in SOURCES if s['source_id']=='ESPN_SITE_SCOREBOARD')['authorization']=='UNVERIFIED'
def test_no_approved_sources(tmp_path): assert evaluate(tmp_path)['approved_live_sources']==[]
def test_no_network(tmp_path): assert evaluate(tmp_path)['network_requests']==0
def test_training_blocked(tmp_path): assert evaluate(tmp_path)['decision']=='BLOCK_TRAINING'
def test_gate_count(tmp_path): assert evaluate(tmp_path)['total_gates']==8
def test_matrix(tmp_path):
    evaluate(tmp_path)
    with (tmp_path/'research/p0_s8/s8_22_2/results/s8_22_2_source_matrix.csv').open() as f: assert len(list(csv.DictReader(f)))==5
def test_prior_report(tmp_path):
    p=tmp_path/'research/p0_s8/s8_22/results/s8_22_report.json';p.parent.mkdir(parents=True);p.write_text('{"http_status":403}')
    r=evaluate(tmp_path);assert r['prior_s822_report']['reported_http_status']==403

def test_bad_prior_report(tmp_path):
    p=tmp_path/'research/p0_s8/s8_22/results/s8_22_report.json';p.parent.mkdir(parents=True);p.write_text('not json')
    assert evaluate(tmp_path)['prior_s822_report']['read_status']=='UNPARSEABLE'
