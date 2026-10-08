import csv
import importlib.util
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_24/run_s7_24.py'
spec=importlib.util.spec_from_file_location('s724',SCRIPT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
HEAD='player_id,player_name,team,valid_from,valid_through,source_name,source_url,source_asof_utc,independent_of_injury_pdf,interval_basis,identity_basis\n'
BASE='123,Test Player,BOS,2026-03-01,2026-03-31,Independent source,https://example.org/record,2026-03-01T10:00:00Z,true,DATED_PRIMARY_EVIDENCE,STABLE_PLAYER_ID\n'
def run(tmp_path, line=BASE):
    source=tmp_path/'source.csv';source.write_text(HEAD+line)
    return m.ingest(source,tmp_path/'out')
def test_empty_is_fail_closed(tmp_path):
    r=run(tmp_path,'');assert r['qualified_evidence_rows']==0 and not r['eligible_for_asof_training']
def test_attested_row_is_staged_not_promoted(tmp_path):
    r=run(tmp_path);assert r['qualified_evidence_rows']==1 and r['decision']=='BLOCK_TRAINING'
    with (tmp_path/'out/s7_24_qualified_evidence.csv').open() as f: rows=list(csv.DictReader(f))
    assert rows[0]['player_id']=='123' and rows[0]['evidence_id'].startswith('S724-')
def test_season_only_rejected(tmp_path):
    r=run(tmp_path,BASE.replace('DATED_PRIMARY_EVIDENCE','SEASON_ROSTER'))
    assert r['rejected_rows']==1
def test_name_only_rejected(tmp_path):
    r=run(tmp_path,BASE.replace('123,Test',' ,Test'))
    assert r['rejected_rows']==1
def test_non_https_rejected(tmp_path):
    r=run(tmp_path,BASE.replace('https://','http://'))
    assert r['rejected_rows']==1
def test_reversed_interval_rejected(tmp_path):
    r=run(tmp_path,BASE.replace('2026-03-01,2026-03-31','2026-04-01,2026-03-31'))
    assert r['rejected_rows']==1
