import importlib.util
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_22/run_s7_22.py'
s=importlib.util.spec_from_file_location('s722',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
BASE={'game_date':'2026-03-27','matchup':'NOP@DET','team':'New Orleans Pelicans'}
def test_valid_team_and_matchup(): assert m.check_row(BASE,BASE)==[]
def test_wrong_team_detected():
    r={**BASE,'team':'Boston Celtics'}
    assert 'TEAM_NOT_IN_MATCHUP' in m.check_row(r,BASE)
def test_wrong_section_detected():
    r={**BASE,'team':'Detroit Pistons'}
    assert 'SECTION_TEAM_MISMATCH' in m.check_row(r,BASE)
def test_invalid_matchup_detected():
    r={**BASE,'matchup':'NOP@XYZ'}
    assert 'INVALID_MATCHUP' in m.check_row(r,BASE)
def test_leakage_gate_fails_closed():
    assert not m.training_allowed({'eligible_for_asof_training':True,'parse_status':'VERIFIED'})
    assert not m.training_allowed({'eligible_for_asof_training':False,'parse_status':'VERIFIED'},True,True,True)
    assert m.training_allowed({'eligible_for_asof_training':True,'parse_status':'VERIFIED'},True,True,True)
