from nba_mike.data.injury_stateful import parse_pages,compare,_cells

def line(y,**kwargs):
    x={'date':25,'time':125,'matchup':200,'team':270,'player':425,'status':585,'reason':670}
    words=[]
    for key,value in kwargs.items():
        cur=x[key]
        for token in value.split(' '):
            words.append((cur,y,cur+len(token)*4,y+8,token,0,0,0))
            cur+=len(token)*4+3
    return words

def pages(*specs):
    return [{'page':i+1,'width':841.95,'words':[w for group in specs[i] for w in group]} for i in range(len(specs))]

def test_cross_page_context():
    data=pages([line(10,date='03/27/2026',matchup='HOU@MEM',team='Houston Rockets',player='Adams, Steven',status='Out',reason='Surgery')],
               [line(10,player='Newton, Tristen',status='Out',reason='Two-Way')])
    rows,_=parse_pages(data,'a')
    assert len(rows)==2
    assert rows[1]['team']=='Houston Rockets' and rows[1]['matchup']=='HOU@MEM'
    assert rows[1]['game_date']=='2026-03-27'

def test_team_switch_same_matchup():
    data=pages([line(10,date='03/27/2026',matchup='HOU@MEM',team='Houston Rockets',player='Adams, Steven',status='Out'),
                line(35,team='Memphis Grizzlies',player='Clarke, Brandon',status='Out')])
    rows,_=parse_pages(data,'a')
    assert rows[1]['team']=='Memphis Grizzlies' and rows[1]['matchup']=='HOU@MEM'

def test_new_matchup_resets_team():
    data=pages([line(10,date='03/27/2026',matchup='HOU@MEM',team='Houston Rockets',player='Adams, Steven',status='Out'),
                line(35,matchup='NOP@TOR',player='Foo, Bar',status='Out')])
    rows,_=parse_pages(data,'a')
    assert rows[1]['team']=='' and rows[1]['matchup']=='NOP@TOR'

def test_date_switch_clears_game_and_team():
    data=pages([line(10,date='03/27/2026',matchup='HOU@MEM',team='Houston Rockets',player='Adams, Steven',status='Out'),
                line(35,date='03/28/2026',player='Foo, Bar',status='Out')])
    rows,_=parse_pages(data,'a')
    assert rows[1]['game_date']=='2026-03-28' and not rows[1]['matchup'] and not rows[1]['team']

def test_submission_not_player():
    data=pages([line(10,date='03/27/2026',matchup='NOP@TOR',team='New Orleans Pelicans',reason='NOT YET SUBMITTED')])
    rows,diag=parse_pages(data,'a')
    assert not rows and diag['not_yet_submitted_sections']==1

def test_header_does_not_create_player():
    rows,_=parse_pages(pages([line(10,player='Player Name',status='Current Status',reason='Reason')]),'a')
    assert not rows

def test_review_only():
    rows,_=parse_pages(pages([line(10,player='Foo, Bar',status='Out')]),'a')
    assert rows[0]['parse_status']=='REVIEW_REQUIRED' and rows[0]['eligible_for_asof_training'] is False

def test_provenance():
    rows,_=parse_pages(pages([line(10,date='03/27/2026',matchup='HOU@MEM',team='Houston Rockets',player='Adams, Steven',status='Out')]),'a')
    assert all('EXPLICIT:p1:' in rows[0][k] for k in ('date_provenance','matchup_provenance','team_provenance'))

def test_compare_recovered():
    old=[{'source_page':'1','player':'Steven Adams','status':'OUT','game_date':'','matchup':'','team':''}]
    new=[{'source_page':1,'player':'Steven Adams','status':'OUT','game_date':'2026-03-27','matchup':'HOU@MEM','team':'Houston Rockets','flags':'REVIEW'}]
    changes,summary=compare(old,new)
    assert len(changes)==1 and summary['recovered_fields']['team']==1

def test_compare_conflict():
    old=[{'source_page':'1','player':'Steven Adams','status':'OUT','game_date':'','matchup':'AAA@BBB','team':''}]
    new=[{'source_page':1,'player':'Steven Adams','status':'OUT','game_date':'','matchup':'HOU@MEM','team':'','flags':'REVIEW'}]
    _,summary=compare(old,new)
    assert summary['conflicting_nonempty_fields']['matchup']==1

def test_compare_duplicate_abstains():
    old=[{'source_page':'1','player':'Steven Adams','status':'OUT'}]*2
    new=[{'source_page':1,'player':'Steven Adams','status':'OUT'}]
    _,summary=compare(old,new)
    assert summary['unmatched_new_rows']==1

def test_page_width_change_resets():
    data=pages([line(10,date='03/27/2026',matchup='HOU@MEM',team='Houston Rockets',player='Adams, Steven',status='Out')],
               [line(10,player='Foo, Bar',status='Out')]);data[1]['width']=845
    rows,diag=parse_pages(data,'a')
    assert not rows[1]['team'] and any(e['type']=='LAYOUT_CHANGE_RESET' for e in diag['events'])
