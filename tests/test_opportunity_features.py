import pandas as pd
import pytest
from nba_mike.features.opportunity import OpportunityFeatureError, build_opportunity_research_frame

def sample():
    return pd.DataFrame([
      ["G1","2025-10-20","P1","T1",20,10,4,2,1],
      ["G2","2025-10-22","P1","T1",30,15,5,3,2],
      ["G3","2025-10-24","P1","T1",40,20,6,4,3],
      ["G4","2025-10-26","P1","T1",10,5,2,1,0],
    ],columns=["game_id","event_date","player_id","team_id","min","pts","reb","ast","fg3m"])

def test_first_row_is_cold_start():
    o=build_opportunity_research_frame(sample())
    assert o.loc[0,"prior_games"]==0 and pd.isna(o.loc[0,"minutes_last3_avg"])
def test_second_row_uses_only_first_game():
    o=build_opportunity_research_frame(sample())
    assert o.loc[1,"minutes_last3_avg"]==20
def test_fourth_row_excludes_own_target_minutes():
    o=build_opportunity_research_frame(sample())
    assert o.loc[3,"minutes_last3_avg"]==30
    assert o.loc[3,"target_minutes"]==10
def test_season_average_is_shifted():
    o=build_opportunity_research_frame(sample())
    assert o.loc[2,"minutes_season_avg"]==25
def test_role_delta():
    o=build_opportunity_research_frame(sample())
    assert o.loc[3,"minutes_role_delta_3_vs_season"]==0
def test_per_minute_rate_is_prior_only():
    o=build_opportunity_research_frame(sample())
    assert o.loc[1,"pts_per_min_last5"]==pytest.approx(.5)
def test_duplicate_rejected():
    x=sample(); x=pd.concat([x,x.iloc[[0]]],ignore_index=True)
    with pytest.raises(OpportunityFeatureError,match="duplicate"): build_opportunity_research_frame(x)
def test_missing_stat_rejected():
    x=sample(); x.loc[0,"min"]=None
    with pytest.raises(OpportunityFeatureError,match="missing"): build_opportunity_research_frame(x)
