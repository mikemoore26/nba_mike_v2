import importlib.util
from pathlib import Path
import pytest

SCRIPT=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_17/run_s8_22_10_17.py'
spec=importlib.util.spec_from_file_location('s8221017',SCRIPT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def sample():
    ledger=[];triage=[]
    for i in range(54):
        is_player=i<44
        ident=f'P-{i+1:03}' if is_player else f'T-{i-43:03}'
        name=f'Player Example{i}' if is_player else 'Team Notice'
        ledger.append(dict(record_id=ident,record_type='PLAYER' if is_player else 'TEAM_SUBMISSION',name_or_notice_candidate=name,team_candidate='BOS',matchup_candidate='BOS@PHI',game_date_candidate=m.DATE,status_candidate='OUT',reason_candidate='Example',page='1',y='100',pdf_context_excerpt=f'{name} OUT'))
        triage.append(dict(record_id=ident,record_type=ledger[-1]['record_type'],name_or_notice_candidate=name,team_candidate='BOS',matchup_candidate='BOS@PHI',game_id_evidence='AUTOMATED_VERIFIED',nba_game_id='0022300194'))
    return ledger,triage

def test_normalize_whitespace(): assert m.normalize_name('  Jane   DOE  ')=='jane doe'
def test_normalize_unicode(): assert m.normalize_name('ＡＢＣ')=='abc'
def test_empty_name(): assert m.candidate_quality('')=='EMPTY'
def test_digit_name(): assert m.candidate_quality('John 42')=='DIGIT_IN_NAME'
def test_single_token(): assert m.candidate_quality('John')=='SINGLE_TOKEN_REVIEW'
def test_plausible_not_verified(): assert m.candidate_quality('John Doe')=='PLAUSIBLE_FORMAT_ONLY'
def test_expected_counts():
    a,b=sample();result=m.analyze(a,b)
    assert len(result)==44 and all(r['training_eligible']=='NO' for r in result)
    assert all(r['player_identity_status']=='NOT_CERTIFIED' for r in result)
    assert all(r['historical_asof']=='NOT_CERTIFIED' for r in result)
def test_duplicate_name_team_flag():
    a,b=sample();a[1]['name_or_notice_candidate']=a[0]['name_or_notice_candidate'];b[1]['name_or_notice_candidate']=a[0]['name_or_notice_candidate']
    result=m.analyze(a,b)
    assert result[0]['name_collision']==result[1]['name_collision']=='YES'
def test_source_excerpt_mismatch():
    a,b=sample();a[0]['pdf_context_excerpt']='some other text'
    assert 'SOURCE_EXCERPT_NAME_MISMATCH' in m.analyze(a,b)[0]['reasons']
def test_game_mapping_flag():
    a,b=sample();b[0]['game_id_evidence']='UNVERIFIED'
    assert 'GAME_MAPPING_UNVERIFIED' in m.analyze(a,b)[0]['reasons']
def test_triage_conflict_fails():
    a,b=sample();b[0]['team_candidate']='NYK'
    with pytest.raises(ValueError,match='disagreement'):m.analyze(a,b)
def test_duplicate_ids_fail():
    a,b=sample();a[1]['record_id']=a[0]['record_id']
    with pytest.raises(ValueError,match='Duplicate'):m.analyze(a,b)
def test_wrong_row_count_fails():
    a,b=sample()
    with pytest.raises(ValueError,match='54'):m.analyze(a[:-1],b)
def test_no_timestamp_inference():
    a,b=sample();r=m.analyze(a,b)[0]
    assert r['publication_time_evidence']=='NOT_PROVIDED_IN_TRUSTED_SOURCE'
def test_team_notices_excluded():
    a,b=sample();assert all(r['record_id'].startswith('P-') for r in m.analyze(a,b))
