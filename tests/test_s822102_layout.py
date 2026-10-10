import importlib.util
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_22_10_2/run_s8_22_10_2.py'
spec=importlib.util.spec_from_file_location('s822102',PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def f(x,y,text):return {'x':x,'y':y,'text':text}

def test_multiline_reason_and_team_submission():
    page=[f(201,136.3,'DAL@WAS'),f(265,136.3,'Dallas'),f(292,136.3,'Mavericks'),f(667,136.3,'NOT'),f(687,136.3,'YET'),f(704,136.3,'SUBMITTED'),f(265,166.3,'Washington'),f(317,166.3,'Wizards'),f(426,166.3,'Wright,'),f(459,166.3,'Delon'),f(587,166.3,'Out'),f(667,159.3,'Injury/Illness'),f(727,159.3,'Left Knee;'),f(667,173.3,'sprain'),f(201,196.4,'BOS@PHI'),f(265,196.4,'Boston'),f(296,196.4,'Celtics'),f(426,196.4,'Brown,'),f(458,196.4,'Jaylen'),f(587,196.4,'Questionable'),f(667,196.4,'Illness')]
    players,teams,issues=m.parse_pages([page])
    assert len(players)==2 and len(teams)==1
    assert teams[0]['team_candidate']=='DAL'
    assert players[0]['team_candidate']=='WAS' and players[0]['matchup_candidate']=='DAL@WAS'
    assert players[0]['player_name_candidate']=='Wright, Delon'
    assert 'sprain' in players[0]['reason_candidate']
    assert players[1]['player_name_candidate']=='Brown, Jaylen'
    assert players[1]['team_candidate']=='BOS'
    assert not issues

def test_unknown_player_status_fails_closed():
    p=[f(201,140,'DAL@WAS'),f(265,140,'Washington'),f(320,140,'Wizards'),f(426,140,'Unknown, X'),f(587,140,'Uncertain')]
    players,teams,issues=m.parse_pages([p]);assert not players and not teams
    assert any(x['issue']=='UNMATCHED_PLAYER_OR_STATUS' for x in issues)

def test_page_context_does_not_silently_carry():
    pages=[[f(201,140,'DAL@WAS'),f(265,140,'Washington'),f(320,140,'Wizards'),f(426,140,'Wright, Delon'),f(587,140,'Out')],[f(426,140,'Other, Player'),f(587,140,'Out')]]
    players,_,issues=m.parse_pages(pages)
    assert len(players)==2 and players[1]['team_candidate']=='' and players[1]['matchup_candidate']==''
    assert any(x['issue']=='MISSING_PAGE_CONTEXT' for x in issues)

def test_conflicting_team_game_is_flagged():
    p=[f(201,140,'DAL@WAS'),f(265,140,'Boston'),f(296,140,'Celtics'),f(426,140,'Brown, Jaylen'),f(587,140,'Out')]
    players,_,issues=m.parse_pages([p]);assert players[0]['team_candidate']==''
    assert any(x['issue']=='TEAM_GAME_CONFLICT' for x in issues)

def test_no_certification_flags():
    p=[f(201,140,'DAL@WAS'),f(265,140,'Washington'),f(320,140,'Wizards'),f(426,140,'Wright, Delon'),f(587,140,'Out')]
    players,_,_=m.parse_pages([p]);assert players[0]['player_verified'] is False
    assert players[0]['historical_asof_certified'] is False
