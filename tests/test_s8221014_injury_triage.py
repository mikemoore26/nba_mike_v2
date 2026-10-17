import importlib.util
from pathlib import Path
import tempfile
import csv
import json
import hashlib
import pytest

SCRIPT=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_14/run_s8_22_10_14.py'
spec=importlib.util.spec_from_file_location('s8221014',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def row(**kw):
    r={'record_id':'P-001','record_type':'PLAYER','game_date_candidate':'2023-11-15','matchup_candidate':'BOS@PHI','team_candidate':'BOS','name_or_notice_candidate':'Example Player','status_candidate':'Out','reason_candidate':'Test','page':'1','y':'300','pdf_context_excerpt':'Example Player Out','parser_header_artifact_flag':'NO'}
    r.update(kw);return r

def test_player_not_certified():
    x=m.triage([row()],{'BOS@PHI':'0022300194'})[0]
    assert x['triage_status']=='EVIDENCE_PENDING' and x['training_eligible']=='NO' and x['historical_asof']=='NOT_CERTIFIED' and x['player_identity']=='NOT_CERTIFIED'

def test_team_submission_not_player():
    x=m.triage([row(record_type='TEAM_SUBMISSION',status_candidate='',name_or_notice_candidate='NOT YET SUBMITTED')],{'BOS@PHI':'0022300194'})[0]
    assert 'TEAM_SUBMISSION_NOT_PLAYER_STATUS' in x['triage_reasons'] and x['injury_status_evidence']=='NOT_CERTIFIED'

def test_bad_matchup_exception():
    x=m.triage([row(matchup_candidate='ATL@NYK')],{'BOS@PHI':'0022300194'})[0]
    assert x['triage_status']=='EXCEPTION_REVIEW_REQUIRED' and x['nba_game_id']==''

def test_bad_team_exception():
    assert 'TEAM_REQUIRES_REVIEW' in m.triage([row(team_candidate='LAL')],{'BOS@PHI':'0022300194'})[0]['triage_reasons']

def test_unknown_status_exception():
    assert 'STATUS_REQUIRES_REVIEW' in m.triage([row(status_candidate='maybe')],{'BOS@PHI':'0022300194'})[0]['triage_reasons']

def test_header_artifact_exception():
    assert 'PARSER_HEADER_ARTIFACT' in m.triage([row(parser_header_artifact_flag='YES')],{'BOS@PHI':'0022300194'})[0]['triage_reasons']

def test_duplicate_ids_fail_closed():
    with pytest.raises(ValueError,match='duplicate'):m.triage([row(),row()],{'BOS@PHI':'0022300194'})

def test_empty_ledger_fail_closed():
    with pytest.raises(ValueError):m.triage([],{})

def test_missing_columns_fail_closed():
    with pytest.raises(ValueError):m.triage([{'record_id':'P-001'}],{})

def test_game_report_csv_validation():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);rp=p/'review.json';cp=p/'automated_game_id_verification.csv'
        rp.write_text(json.dumps({'milestone':'S8.22.10.13','crosswalk_sha256':m.EXPECTED_CROSSWALK_SHA,'automated_verified':8,'manual_exceptions':0,'training_decision':'BLOCK_TRAINING'}))
        with cp.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['game_date','away_at_home','nba_game_id','verification_status']);w.writeheader()
            for matchup,gid in m.EXPECTED_GAME_IDS.items():w.writerow({'game_date':m.DATE,'away_at_home':matchup,'nba_game_id':gid,'verification_status':'AUTOMATED_VERIFIED'})
        games,_=m.validate_game_report(rp);assert games==m.EXPECTED_GAME_IDS
        with cp.open('a') as f:f.write('2023-11-15,BOS@PHI,0022300194,AUTOMATED_VERIFIED\n')
        with pytest.raises(ValueError):m.validate_game_report(rp)

def test_find_ledger_by_verified_crosswalk_hash():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d);base=root/'research/p0_s8/s8_22_10_7/results/2023-11-15/wrong_folder';base.mkdir(parents=True)
        (base/'provisional_game_id_crosswalk.csv').write_text('example')
        (base/'player_and_team_manual_review.csv').write_text('example')
        with pytest.raises(ValueError):m.discover_ledger(root)

def test_wrong_report_governance_fails():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'review.json';p.write_text(json.dumps({'milestone':'S8.22.10.13','training_decision':'ALLOW_TRAINING'}))
        with pytest.raises(ValueError):m.validate_game_report(p)
