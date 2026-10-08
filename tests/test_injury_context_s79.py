import pytest
from nba_mike.data.injury_context_audit import explicit_context,collect_evidence,propose

def line(y,words):
    x=0;result=[]
    for word in words.split():
        result.append((x,y,x+len(word)*5,y+8,word));x+=len(word)*5+5
    return {'y':y+4,'words':result}

def test_explicit_date():
    assert explicit_context(line(10,'03/27/2026')['words'] if False else line(10,'03/27/2026'))['game_date']=='2026-03-27'
def test_explicit_matchup():
    assert explicit_context(line(10,'MIA@CLE'))['matchup']=='MIA@CLE'
def test_explicit_team():
    assert explicit_context(line(10,'Miami Heat'))['team']=='Miami Heat'
def test_missing_context_unresolved():
    r=[{'source_page':'2','source_y':'90','player':'A','status':'OUT','game_date':'','matchup':'','team':''}]
    assert propose(r,[])[0]['decision']=='UNRESOLVED'
def test_same_page_prior_matchup_proposed():
    r=[{'source_page':'2','source_y':'90','player':'A','status':'OUT','game_date':'','matchup':'','team':''}]
    e=[{'page':2,'y':50,'game_date':'','matchup':'MIA@CLE','team':'','text':'MIA@CLE'}]
    p=propose(r,e)[0]
    assert p['candidate_matchup']=='MIA@CLE' and p['decision']=='REVIEW_PROPOSAL_NOT_APPLIED'
def test_future_context_not_used():
    r=[{'source_page':'2','source_y':'40','player':'A','status':'OUT','game_date':'','matchup':'','team':''}]
    e=[{'page':2,'y':50,'game_date':'','matchup':'MIA@CLE','team':'','text':'MIA@CLE'}]
    assert propose(r,e)[0]['decision']=='UNRESOLVED'
def test_other_page_context_not_used():
    r=[{'source_page':'2','source_y':'90','player':'A','status':'OUT','game_date':'','matchup':'','team':''}]
    e=[{'page':1,'y':50,'game_date':'','matchup':'MIA@CLE','team':'','text':'MIA@CLE'}]
    assert propose(r,e)[0]['decision']=='UNRESOLVED'
def test_existing_values_not_overwritten():
    r=[{'source_page':'2','source_y':'90','player':'A','status':'OUT','game_date':'2026-03-27','matchup':'MIA@CLE','team':'Miami Heat'}]
    assert propose(r,[])==[]
def test_partial_team_only():
    r=[{'source_page':'2','source_y':'90','player':'A','status':'OUT','game_date':'','matchup':'','team':'Miami Heat'}]
    e=[{'page':2,'y':50,'game_date':'','matchup':'MIA@CLE','team':'Cleveland Cavaliers','text':'Cleveland Cavaliers MIA@CLE'}]
    p=propose(r,e)[0]
    assert p['candidate_matchup']=='MIA@CLE' and p['candidate_team']==''
def test_empty_page_trace():
    e,t=collect_evidence([{'page':1,'width':612,'words':[]}])
    assert e==[] and t==[]
def test_no_columns_no_trace():
    e,t=collect_evidence([{'page':1,'width':612,'words':line(10,'hello there')['words']}])
    assert t==[]
def test_date_without_matchup_is_only_proposal():
    r=[{'source_page':'1','source_y':'90','player':'A','status':'OUT','game_date':'','matchup':'','team':''}]
    e=[{'page':1,'y':50,'game_date':'2026-03-27','matchup':'','team':'','text':'03/27/2026'}]
    p=propose(r,e)[0]
    assert p['candidate_game_date']=='2026-03-27' and p['decision']!='VERIFIED'
