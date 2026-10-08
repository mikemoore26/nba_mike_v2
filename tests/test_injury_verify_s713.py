import pytest
from nba_mike.data.injury_verify import ABBR, normalize_team_name, team_in_matchup, verify

@pytest.mark.parametrize('abbr,canonical', sorted(ABBR.items()))
def test_all_30_canonical_names(abbr, canonical):
    assert normalize_team_name(canonical) == abbr
    assert normalize_team_name(abbr) == abbr
    assert team_in_matchup(canonical, f'{abbr}@BOS')
    assert team_in_matchup(canonical, f'BOS@{abbr}')

def test_all_thirty_teams():
    assert len(ABBR) == 30

def test_clippers_aliases():
    for name in ('LA Clippers','Los Angeles Clippers','  la   clippers  '):
        assert normalize_team_name(name) == 'LAC'
        assert team_in_matchup(name,'LAC@IND')

def test_wrong_team_still_fails():
    assert not team_in_matchup('Chicago Bulls','LAC@IND')

def test_unknown_and_invalid():
    assert normalize_team_name('Imaginary Team') is None
    assert not team_in_matchup('LA Clippers','XYZ@IND')
    assert not team_in_matchup('LA Clippers','LAC-IND')

def test_no_player_roster_inference():
    assert normalize_team_name('Bradley Beal') is None

def test_real_flag_shape_no_false_positive():
    row={'source_page':'1','source_y':'100','player':'Bradley Beal','status':'OUT',
         'game_date':'2026-03-27','matchup':'LAC@IND','team':'LA Clippers',
         'date_provenance':'EXPLICIT:p1:y10.0','matchup_provenance':'EXPLICIT:p1:y10.0',
         'team_provenance':'EXPLICIT:p1:y10.0','parse_status':'REVIEW_REQUIRED',
         'eligible_for_asof_training':'False'}
    events=[{'page':'1','y':'10.0','type':t,'value':v} for t,v in
        [('DATE','2026-03-27'),('MATCHUP','LAC@IND'),('TEAM','LA Clippers')]]
    _, report=verify([row],events)
    assert report['flagged_records']==0
