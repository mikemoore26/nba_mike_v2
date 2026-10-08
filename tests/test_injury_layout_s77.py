from nba_mike.data.injury_layout import parse_word_pages

def w(x,y,s): return (x,y,x+max(8,len(s)*5),y+9,s,0,0,0)
def header(): return [w(120,0,'Team'),w(220,0,'Player'),w(275,0,'Name'),w(380,0,'Current'),w(440,0,'Status'),w(530,0,'Reason')]
def record(y=20): return [w(220,y,'Smith,'),w(265,y,'Jane'),w(440,y,'Out'),w(530,y,'Knee')]
def pg(i,words): return {'page':i,'words':words,'width':750}
def first(): return pg(1,header()+[w(10,20,'03/27/2026'),w(70,20,'LAC@IND')]+record())

def test_backfill_date_when_matchup_explicit():
    rows,d=parse_word_pages([first(),pg(2,[w(70,20,'MIA@CLE')]+record())],'sha')
    assert rows[1]['game_date']=='2026-03-27'
    assert rows[1]['date_provenance']=='DOCUMENT_UNIQUE_DATE_INFERRED'
    assert d['date_backfills']==1
    assert 'DATE_INFERRED_REVIEW_REQUIRED' in rows[1]['flags']
    assert rows[1]['parse_status']=='REVIEW_REQUIRED'

def test_no_matchup_no_backfill():
    rows,d=parse_word_pages([first(),pg(2,record())],'sha')
    assert rows[1]['game_date']==''
    assert rows[1]['team']==''
    assert d['date_backfills']==0

def test_conflicting_dates_disable_backfill():
    rows,d=parse_word_pages([first(),pg(2,[w(10,20,'03/28/2026'),w(70,20,'MIA@CLE')]+record()),pg(3,[w(70,20,'ATL@BOS')]+record())],'sha')
    assert d['date_conflicts'] is True
    assert rows[-1]['game_date']==''

def test_no_date_anywhere():
    rows,d=parse_word_pages([pg(1,header()+[w(70,20,'LAC@IND')]+record())],'sha')
    assert d['document_dates']==[] and rows[0]['game_date']==''

def test_explicit_date_not_overwritten():
    rows,d=parse_word_pages([first(),pg(2,[w(10,20,'03/27/2026'),w(70,20,'MIA@CLE')]+record())],'sha')
    assert rows[1]['date_provenance']=='EXPLICIT_ROW_CONTEXT'
    assert d['date_backfills']==0

def test_training_always_blocked():
    rows,_=parse_word_pages([first(),pg(2,[w(70,20,'MIA@CLE')]+record())],'sha')
    assert all(r['eligible_for_asof_training'] is False for r in rows)

def test_date_inference_keeps_team_unresolved():
    rows,_=parse_word_pages([first(),pg(2,[w(70,20,'MIA@CLE')]+record())],'sha')
    assert rows[1]['team']=='' and 'TEAM_UNRESOLVED' in rows[1]['flags']

def test_page_date_counts():
    _,d=parse_word_pages([first(),pg(2,[w(70,20,'MIA@CLE')]+record())],'sha')
    assert d['per_page'][1]['date_inferred']==1
