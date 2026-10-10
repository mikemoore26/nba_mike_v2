import importlib.util
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_3/run_s8_22_10_3.py'
spec=importlib.util.spec_from_file_location('s822103',SCRIPT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def token(x,y,text):return {'x':x,'y':y,'text':text}

def test_page_2_trent_inherits_toronto_and_matchup():
    p1=[token(201,140,'MIL@TOR'),token(265,150,'Toronto'),token(301,150,'Raptors'),token(426,480,'Anunoby,'),token(467,480,'OG'),token(586,480,'Doubtful'),token(667,480,'Finger')]
    p2=[token(426,155,'Trent'),token(451,155,'Jr.,'),token(465,155,'Gary'),token(586,155,'Doubtful'),token(667,148,'Right'),token(667,162,'fasciitis'),token(201,185,'NYK@ATL'),token(265,185,'New'),token(286,185,'York'),token(306,185,'Knicks'),token(426,185,'Barrett,'),token(459,185,'RJ'),token(586,185,'Questionable'),token(667,185,'Migraine')]
    players,_,issues=m.parse_pages([p1,p2]); assert players[1]['team_candidate']=='TOR'; assert players[1]['matchup_candidate']=='MIL@TOR'; assert players[1]['context_origin']=='CROSS_PAGE_CONTINUATION'; assert players[2]['team_candidate']=='NYK'; assert players[2]['context_origin']=='SAME_PAGE_OR_PRIOR_CONTEXT'; assert not issues

def test_footer_is_excluded():
    players,_,issues=m.parse_pages([[token(425,545.4,'1'),token(430,545.4,'of'),token(438,545.4,'4')]])
    assert players==[] and issues==[]

def test_page_four_new_team_cannot_inherit_incompatible_matchup():
    p1=[token(201,150,'SAC@LAL'),token(265,150,'Sacramento'),token(311,150,'Kings'),token(426,160,'Len,'),token(445,160,'Alex'),token(586,160,'Out'),token(667,160,'Sprain')]
    p2=[token(265,137,'Miami'),token(294,137,'Heat'),token(667,137,'NOT'),token(688,137,'YET'),token(705,137,'SUBMITTED'),token(201,160,'OKC@GSW'),token(265,160,'Oklahoma'),token(309,160,'City'),token(327,160,'Thunder'),token(667,160,'NOT'),token(688,160,'YET'),token(705,160,'SUBMITTED')]
    _,subs,issues=m.parse_pages([p1,p2]); assert subs[0]['team_candidate']=='MIA'; assert subs[0]['matchup_candidate']==''; assert subs[1]['matchup_candidate']=='OKC@GSW'; assert subs[1]['slate_scope']=='OUTSIDE_VALIDATED_EIGHT_GAME_SLATE'; assert any(x['issue']=='TEAM_MATCHUP_CONFLICT' for x in issues)

def test_outside_slate_not_falsely_validated():
    players,_,_=m.parse_pages([[token(201,136,'OKC@GSW'),token(265,136,'Golden'),token(297,136,'State'),token(321,136,'Warriors'),token(426,136,'Example,'),token(467,136,'Player'),token(586,136,'Out'),token(667,136,'Illness')]])
    assert players[0]['slate_scope']=='OUTSIDE_VALIDATED_EIGHT_GAME_SLATE'

def test_no_context_stays_unresolved():
    players,_,issues=m.parse_pages([[token(426,136,'Unknown,'),token(466,136,'Person'),token(586,136,'Out'),token(667,136,'Illness')]])
    assert players[0]['team_candidate']=='' and players[0]['slate_scope']=='UNRESOLVED'; assert any(x['issue']=='MISSING_CONTEXT' for x in issues)
