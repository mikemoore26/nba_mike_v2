import importlib.util
from pathlib import Path
import csv
import json
import pytest
P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_15/run_s8_22_10_15.py'
spec=importlib.util.spec_from_file_location('s815',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def row(**kw):
    d={'record_id':'x','record_type':'PLAYER','game_date_candidate':m.DATE,'matchup_candidate':'','team_candidate':'BOS','nba_game_id':'','source_page':'1','source_pdf_context':'example'};d.update(kw);return d
@pytest.mark.parametrize('team,matchup', [('BOS','BOS@PHI'),('PHI','BOS@PHI'),('CLE','CLE@POR'),('POR','CLE@POR'),('DAL','DAL@WAS'),('WAS','DAL@WAS'),('MIL','MIL@TOR'),('TOR','MIL@TOR'),('MIN','MIN@PHX'),('PHX','MIN@PHX'),('NYK','NYK@ATL'),('ATL','NYK@ATL'),('ORL','ORL@CHI'),('CHI','ORL@CHI'),('SAC','SAC@LAL'),('LAL','SAC@LAL')])
def test_unique_team_mapping(team,matchup):
    x=m.classify(row(team_candidate=team));assert x['suggested_matchup']==matchup;assert x['mapping_resolution']=='DETERMINISTIC_MAPPING_CANDIDATE';assert x['training_eligible']=='NO'
def test_bad_date_never_repaired():assert m.classify(row(game_date_candidate='2023-11-16'))['mapping_resolution']=='MANUAL_EXCEPTION_REQUIRED'
def test_wrong_team_never_repaired():assert m.classify(row(team_candidate='XYZ'))['mapping_resolution']=='MANUAL_EXCEPTION_REQUIRED'
def test_conflicting_valid_matchup():assert m.classify(row(matchup_candidate='DAL@WAS'))['reason']=='CONFLICTING_MATCHUP_AND_TEAM'
def test_nonempty_unrecognized_matchup():assert m.classify(row(matchup_candidate='BOS@NYK'))['reason']=='UNRECOGNIZED_NONEMPTY_MATCHUP'
def test_never_certifies():
    x=m.classify(row());assert x['historical_asof']=='NOT_CERTIFIED' and x['player_identity']=='NOT_CERTIFIED' and x['injury_status_evidence']=='NOT_CERTIFIED'
def test_rejects_unexpected_exception_count(tmp_path):
    root=tmp_path;d=root/'research/p0_s8/s8_22_10_14/results/2023-11-15/token';d.mkdir(parents=True)
    (d/'review.json').write_text(json.dumps({'milestone':'S8.22.10.14','records_total':54,'training_decision':'BLOCK_TRAINING'}))
    for name in ('injury_evidence_triage.csv','exception_queue.csv'):
        with (d/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(row())+['triage_status','triage_reasons','game_id_evidence']);w.writeheader()
    with pytest.raises(ValueError,match='Unexpected row counts'):m.run(root,d/'review.json')
