from nba_mike.data.injury_verify import verify

def fixture(team='Houston Rockets',matchup='HOU@MEM',date='2026-03-27',p=2,provenance_page=1):
    row={'source_page':str(p),'source_y':'100','player':'Steven Adams','status':'OUT','game_date':date,'matchup':matchup,'team':team,'date_provenance':f'EXPLICIT:p{provenance_page}:y10.0','matchup_provenance':f'EXPLICIT:p{provenance_page}:y10.0','team_provenance':f'EXPLICIT:p{provenance_page}:y10.0','parse_status':'REVIEW_REQUIRED','eligible_for_asof_training':'False'}
    events=[{'page':str(provenance_page),'y':'10.0','type':k,'value':v} for k,v in [('DATE','2026-03-27'),('MATCHUP','HOU@MEM'),('TEAM','Houston Rockets')]]
    return row,events

def test_valid_cross_page():
    r,e=fixture();rows,s=verify([r],e);assert s['flagged_records']==0 and s['cross_page_review']==1

def test_wrong_team():
    r,e=fixture(team='Chicago Bulls');rows,s=verify([r],e);assert 'TEAM_NOT_IN_MATCHUP' in rows[0]['issues']

def test_unknown_matchup():
    r,e=fixture(matchup='XYZ@MEM');rows,s=verify([r],e);assert 'TEAM_NOT_IN_MATCHUP' in rows[0]['issues']

def test_invalid_matchup():
    r,e=fixture(matchup='garbage');rows,s=verify([r],e);assert 'MATCHUP_MISSING_OR_INVALID' in rows[0]['issues']

def test_date_mismatch():
    r,e=fixture(date='2026-03-28');rows,s=verify([r],e);assert 'DATE_CONTRADICTS_EXPLICIT_EVENT' in rows[0]['issues']

def test_future_provenance():
    r,e=fixture(p=1,provenance_page=2);rows,s=verify([r],e);assert 'TEAM_PROVENANCE_IN_FUTURE' in rows[0]['issues']

def test_missing_provenance():
    r,e=fixture();r['team_provenance']='';rows,s=verify([r],e);assert 'TEAM_PROVENANCE_INVALID' in rows[0]['issues']

def test_duplicate():
    r,e=fixture();rows,s=verify([r,r.copy()],e);assert s['flagged_records']==2

def test_unsafe_label():
    r,e=fixture();r['eligible_for_asof_training']='True';rows,s=verify([r],e);assert 'UNSAFE_TRAINING_LABEL' in rows[0]['issues']

def test_no_prior_date():
    r,e=fixture();e=[x for x in e if x['type']!='DATE'];rows,s=verify([r],e);assert 'NO_PRIOR_EXPLICIT_DATE_EVENT' in rows[0]['issues']

def test_same_page_spot_check():
    r,e=fixture(p=1,provenance_page=1);rows,s=verify([r],e);assert s['spot_check']==1

def test_empty():
    rows,s=verify([],[]);assert s['records']==0
