import importlib.util
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_5/run_s8_22_10_5.py'
spec=importlib.util.spec_from_file_location('review105',SOURCE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_exact_match():
    assert m.schedule_check('2023-11-15','DAL@WAS')=='EXACT_PRIOR_SLATE_MATCH'

def test_reversed_orientation():
    assert m.schedule_check('2023-11-15','MIN@PHX')=='REVERSED_HOME_AWAY_CONFLICT'

def test_outside_date():
    assert m.schedule_check('2023-11-16','BKN@MIA')=='OUTSIDE_TARGET_DATE'

def test_unrecognized():
    assert m.schedule_check('2023-11-15','???')=='INVALID_OR_MISSING_MATCHUP'

def test_no_auto_verification():
    players=[{'page':'1','y':'115.2','game_date_candidate':'2023-11-15','matchup_candidate':'DAL@WAS',
              'team_candidate':'DAL','player_name_candidate':'Player Name','status_candidate':'Current Status'}]
    ledger=m.make_ledger(players,[],[[(115.2,426,'Player Name'),(115.2,587,'Current Status')]])
    assert ledger[0]['parser_header_artifact_flag']=='YES'
    assert ledger[0]['manual_decision']=='PENDING'
    assert ledger[0]['training_eligible']=='NO'
    assert ledger[0]['historical_asof_certified']=='NO'

def test_preserves_source_fields():
    players=[{'page':'2','y':'155.1','game_date_candidate':'2023-11-15','matchup_candidate':'MIL@TOR',
              'team_candidate':'TOR','player_name_candidate':'Trent Jr., Gary','status_candidate':'Doubtful',
              'reason_candidate':'Injury/Illness - Right Foot; plantar fasciitis'}]
    ledger=m.make_ledger(players,[],[[],[(155.1,426,'Trent Jr., Gary')]])
    assert ledger[0]['name_or_notice_candidate']=='Trent Jr., Gary'
    assert ledger[0]['verified_name_or_notice']==''
