import pytest
from nba_mike.data.injury_audit import audit
SHA='a'*64

def row(page='2',player='Jane Doe',team='Miami Heat',matchup='MIA@CLE',date='',status='OUT',reason='Rest',provenance='UNRESOLVED',flags=''):
    return dict(source_sha256=SHA,source_page=page,player=player,team=team,matchup=matchup,game_date=date,status=status,reason=reason,date_provenance=provenance,flags=flags)

def test_missing_date():
    x=audit([],[],[row()],SHA);assert x['counts']['missing_date']==1

def test_inferred_date_not_verified():
    x=audit([],[],[row(date='2026-03-27',provenance='DOCUMENT_UNIQUE_DATE_INFERRED')],SHA);assert x['counts']['inferred_date']==1 and x['decision']=='BLOCK_TRAINING'

def test_team_mismatch():
    x=audit([],[],[row(team='Boston Celtics')],SHA);assert x['counts']['high_priority_disagreements']==1

def test_valid_matchup():
    x=audit([],[],[row(date='2026-03-27')],SHA);assert x['counts']['high_priority_disagreements']==0

def test_status_disagreement():
    x=audit([row(status='OUT')],[],[row(status='QUESTIONABLE')],SHA);assert x['counts']['high_priority_disagreements']==1

def test_matching_status():
    x=audit([row(status='OUT')],[],[row(status='OUT')],SHA);assert x['cross_parser_status_agreement']['s7_4_STATUS_MATCH']==1

def test_duplicates():
    x=audit([],[],[row(),row()],SHA);assert x['counts']['high_priority_disagreements']==2

def test_sha_mismatch():
    r=row();r['source_sha256']='bad'
    with pytest.raises(ValueError):audit([],[],[r],SHA)

def test_sample_limit():
    x=audit([],[],[row(player=str(i)) for i in range(20)],SHA,sample_size=5);assert x['counts']['sample_size']==5

def test_sample_spans_pages():
    x=audit([],[],[row(page='2'),row(page='3',player='Other'),row(page='4',player='Third')],SHA,sample_size=3);assert len({r['page'] for r in x['review_sample']})==3

def test_invalid_sample():
    with pytest.raises(ValueError):audit([],[],[],SHA,sample_size=0)

def test_missing_reason():
    x=audit([],[],[row(reason='')],SHA);assert 'MISSING_REASON' in x['review_sample'][0]['issues']
