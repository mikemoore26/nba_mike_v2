import pandas as pd
import pytest
from nba_mike.features.opportunity import OpportunityFeatureError,build_opportunity_research_frame

C=["game_id","event_date","player_id","team_id","min","pts","reb","ast","fg3m"]
def rows():
    return pd.DataFrame([
      ["A","2025-10-20","P","T",20,10,4,2,1],
      ["B","2025-10-22","P","T",30,15,5,3,2],
      ["C","2025-10-22","P","T",40,20,6,4,3],
      ["D","2025-10-24","P","T",10,5,2,1,0],
    ],columns=C)
def test_same_date_cannot_leak():
    x=build_opportunity_research_frame(rows())
    b=x.set_index("game_id").loc["B"]
    c=x.set_index("game_id").loc["C"]
    assert b["minutes_last3_avg"]==c["minutes_last3_avg"]==20
    assert b["prior_games"]==c["prior_games"]==1
def test_next_date_sees_prior_dates():
    x=build_opportunity_research_frame(rows()).set_index("game_id")
    assert x.loc["D","prior_games"]==3
    assert x.loc["D","minutes_last3_avg"]==pytest.approx(27.5)
def test_future_changes_do_not_affect_past():
    x=rows()
    before=build_opportunity_research_frame(x).set_index("game_id").loc["B","minutes_last3_avg"]
    x.loc[x.game_id=="D","min"]=55
    after=build_opportunity_research_frame(x).set_index("game_id").loc["B","minutes_last3_avg"]
    assert before==after
def test_infinite_rejected():
    x=rows();x["min"]=x["min"].astype(float);x.loc[0,"min"]=float("inf")
    with pytest.raises(OpportunityFeatureError,match="nonfinite"): build_opportunity_research_frame(x)
def test_negative_count_rejected():
    x=rows();x.loc[0,"pts"]=-1
    with pytest.raises(OpportunityFeatureError,match="negative"): build_opportunity_research_frame(x)

