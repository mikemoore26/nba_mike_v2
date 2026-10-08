from nba_mike.data.injury_auto import parse_lines
SHA='a'*64

def page(lines):return [{'page':1,'text':'\n'.join(lines)}]

def test_complete_row():
    rows,bad=parse_lines(page(['03/27/2026 07:00 (ET) LAC@IND LA Clippers Beal, Bradley Out Injury/Illness - Left Hip; Pain']),SHA)
    assert len(rows)==1 and not bad
    assert rows[0]['player']=='Bradley Beal'
    assert rows[0]['team']=='LA Clippers'
    assert rows[0]['game_date']=='2026-03-27'
    assert rows[0]['status']=='OUT'
    assert rows[0]['eligible_for_asof_training'] is False

def test_context_continuation():
    rows,bad=parse_lines(page(['03/27/2026 LAC@IND LA Clippers Beal, Bradley Out Injury/Illness - Left Hip',
                              'Leonard, Kawhi Questionable Injury/Illness - Right Knee']),SHA)
    assert len(rows)==2 and rows[1]['team']=='LA Clippers'

def test_missing_player_abstains():
    rows,bad=parse_lines(page(['03/27/2026 LAC@IND LA Clippers Out Injury/Illness - Knee']),SHA)
    assert len(bad)==1 and 'PLAYER_UNRESOLVED' in rows[0]['flags']

def test_no_context_across_pages():
    rows,bad=parse_lines([{'page':1,'text':'03/27/2026 LAC@IND LA Clippers Beal, Bradley Out Injury/Illness - Hip'},
                          {'page':2,'text':'Leonard, Kawhi Out Injury/Illness - Knee'}],SHA)
    assert 'TEAM_UNRESOLVED' in rows[1]['flags']

def test_no_status_no_record():
    rows,_=parse_lines(page(['Header: Injury Report','Some explanation text']),SHA)
    assert rows==[]

def test_unusual_reason_review():
    rows,bad=parse_lines(page(['03/27/2026 LAC@IND LA Clippers Beal, Bradley Out Unclear']),SHA)
    assert len(bad)==1 and 'REASON_FORMAT_UNVERIFIED' in rows[0]['flags']

def test_stable_id():
    x=page(['03/27/2026 LAC@IND LA Clippers Beal, Bradley Out Injury/Illness - Hip'])
    assert parse_lines(x,SHA)[0][0]['record_id']==parse_lines(x,SHA)[0][0]['record_id']

def test_team_does_not_falsely_match_substring():
    rows,bad=parse_lines(page(['03/27/2026 LAC@IND LA Clippers Beal, Bradley Out Injury/Illness - Hip']),SHA)
    assert rows[0]['team']=='LA Clippers'
