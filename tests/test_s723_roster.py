import importlib.util
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_23/run_s7_23.py'
spec=importlib.util.spec_from_file_location('s723',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
R={'player':'Test Player','team':'Boston Celtics','game_date':'2026-03-27'}
def e(team='Boston Celtics',**kw):
    return dict(player_id='123',player_name='Test Player',team=team,valid_from='2026-03-01',valid_through='2026-03-31',source_name='Independent roster',source_url='https://example.org/roster',retrieved_utc='2026-10-08T20:00:00Z',source_asof_utc='2026-03-27T10:00:00Z',evidence_id='E1',independent_of_injury_pdf='true',**kw)
def test_missing_evidence_unresolved():assert m.verify(R,[])[0]=='UNRESOLVED'
def test_independent_match_verified():assert m.verify(R,[e()])[0]=='VERIFIED'
def test_trade_team_conflict():assert m.verify(R,[e(team='New York Knicks')])[0]=='CONFLICT'
def test_stale_roster_unresolved():
    x=e();x['valid_through']='2026-03-20';assert m.verify(R,[x])[0]=='UNRESOLVED'
def test_self_reported_not_independent():
    x=e();x['independent_of_injury_pdf']='false';assert m.verify(R,[x])[0]=='UNRESOLVED'
def test_conflicting_sources():
    a=e();b=e(team='New York Knicks');b['evidence_id']='E2';assert m.verify(R,[a,b])[0]=='CONFLICT'
def test_ambiguous_ids():
    a=e();b=e();b['player_id']='456';assert m.verify(R,[a,b])[1]=='AMBIGUOUS_PLAYER_ID'
