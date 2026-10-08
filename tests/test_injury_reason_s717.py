from nba_mike.data.injury_reason_recovery import recover_page


def word(x,y,s):
    return (x,y-4,x+len(s)*4,y+4,s,0,0,0)


def row(y,reason='',player='Test Player'):
    return {'record_id':str(y),'source_sha256':'abc','source_page':1,'source_y':y,
            'player':player,'status':'OUT','reason':reason}


def test_same_line_reason():
    r=recover_page([row(100)],[word(670,100,'Injury/Illness'),word(725,100,'-'),word(740,100,'Knee')])
    assert r[0]['decision']=='PROPOSED_REVIEW_REQUIRED'
    assert r[0]['proposed_reason']=='Injury/Illness - Knee'


def test_wrap_reason():
    r=recover_page([row(100)],[word(670,100,'Injury/Illness'),word(725,100,'-'),word(740,100,'Left'),word(670,111,'Knee;'),word(700,111,'Strain')])
    assert r[0]['proposed_reason']=='Injury/Illness - Left Knee; Strain'


def test_next_player_not_borrowed():
    r=recover_page([row(100),row(120,player='Next')],[word(670,120,'Injury/Illness'),word(730,120,'-')])
    assert r[0]['decision']=='UNRESOLVED'


def test_nonempty_unchanged():
    r=recover_page([row(100,'G League - Two-Way')],[word(670,100,'Injury/Illness')])
    assert r[0]['decision']=='UNCHANGED' and not r[0]['proposed_reason']


def test_no_words_unresolved():
    assert recover_page([row(100)],[])[0]['decision']=='UNRESOLVED'


def test_bad_prefix_unresolved():
    assert recover_page([row(100)],[word(670,100,'Current'),word(720,100,'Status')])[0]['decision']=='UNRESOLVED'


def test_not_recover_from_player_lane():
    assert recover_page([row(100)],[word(450,100,'Injury/Illness')])[0]['decision']=='UNRESOLVED'


def test_scaled_page_width():
    assert recover_page([row(100)],[word(670,100,'Injury/Illness'),word(725,100,'-')],width=1683.9)[0]['decision']=='UNRESOLVED'


def test_no_cross_page_borrow():
    assert recover_page([row(100)],[])[0]['decision']=='UNRESOLVED'
