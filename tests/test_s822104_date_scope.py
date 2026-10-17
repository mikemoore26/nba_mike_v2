import importlib.util
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_4/run_s8_22_10_4.py'
spec=importlib.util.spec_from_file_location('s822104',SCRIPT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def t(x,y,v):return {'x':x,'y':y,'text':v}
def notice(y):return [t(667,y,'NOT'),t(688,y,'YET'),t(705,y,'SUBMITTED')]

def test_date_switch_and_page_four_notices():
    p3=[t(24,136,'11/15/2023'),t(201,401,'SAC@LAL'),t(265,401,'Sacramento'),t(318,401,'Kings'),t(426,401,'Ford,'),t(452,401,'Jordan'),t(586,401,'Out'),t(667,401,'Two-Way')]
    p4=[t(265,90.9,'Los'),t(281,90.9,'Angeles'),t(315,90.9,'Lakers'),*notice(90.9),t(24,114,'11/16/2023'),t(201,114,'BKN@MIA'),t(265,114,'Brooklyn'),t(303,114,'Nets'),*notice(114),t(265,137,'Miami'),t(294,137,'Heat'),*notice(137),t(201,160,'OKC@GSW'),t(265,160,'Oklahoma'),t(309,160,'City'),t(327,160,'Thunder'),*notice(160),t(265,183.1,'Golden'),t(297,183.1,'State'),t(321,183.1,'Warriors'),*notice(183.1)]
    players,subs,issues=m.parse_pages([p3,p4]);assert len(players)==1; assert len(subs)==5
    assert [(s['game_date_candidate'],s['matchup_candidate'],s['team_candidate']) for s in subs]==[
        ('2023-11-15','SAC@LAL','LAL'),('2023-11-16','BKN@MIA','BKN'),('2023-11-16','BKN@MIA','MIA'),('2023-11-16','OKC@GSW','OKC'),('2023-11-16','OKC@GSW','GSW')]
    assert subs[0]['slate_scope']=='IN_VALIDATED_EIGHT_GAME_SLATE'
    assert all(s['slate_scope']=='OUTSIDE_VALIDATED_EIGHT_GAME_SLATE' for s in subs[1:]);assert not issues

def test_same_matchup_different_date_is_out_of_scope():
    p=[t(24,136,'11/16/2023'),t(201,136,'SAC@LAL'),t(265,136,'Los'),t(281,136,'Angeles'),t(315,136,'Lakers'),*notice(136)]
    _,subs,_=m.parse_pages([p]);assert subs[0]['slate_scope']=='OUTSIDE_VALIDATED_EIGHT_GAME_SLATE'

def test_unknown_date_does_not_certify_scope():
    p=[t(201,136,'SAC@LAL'),t(265,136,'Los'),t(281,136,'Angeles'),t(315,136,'Lakers'),*notice(136)]
    _,subs,_=m.parse_pages([p]);assert subs[0]['slate_scope']=='UNRESOLVED'

def test_cross_page_player_inherits_date():
    p1=[t(24,136,'11/15/2023'),t(201,136,'MIL@TOR'),t(265,136,'Toronto'),t(300,136,'Raptors'),t(426,136,'Example,'),t(465,136,'A'),t(586,136,'Out'),t(667,136,'Injury')]
    p2=[t(426,155,'Trent'),t(451,155,'Jr.,'),t(465,155,'Gary'),t(586,155,'Doubtful'),t(667,155,'Injury')]
    players,_,issues=m.parse_pages([p1,p2]);assert len(players)==2;assert players[1]['game_date_candidate']=='2023-11-15';assert players[1]['team_candidate']=='TOR';assert not issues

def test_footer_and_title_not_records():
    players,subs,issues=m.parse_pages([[t(288,62,'Injury'),t(398,545.4,'Page'),t(420,545.4,'1'),t(438,545.4,'4')]])
    assert not players and not subs and not issues
