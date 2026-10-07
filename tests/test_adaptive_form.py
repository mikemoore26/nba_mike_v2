import pandas as pd
import pytest
from nba_mike.features.adaptive_form import make_form_frame, expanding_prequential, score_forecasts, CANDIDATES


def sample():
    rows=[]
    for i in range(45):
        rows.append(dict(game_id=f"g{i}", event_date=pd.Timestamp("2025-01-01")+pd.Timedelta(days=i),player_id="A",min=20+i%8))
    return pd.DataFrame(rows)


def test_same_date_d1():
    x=sample()
    extra=x.iloc[[2]].copy();extra.loc[:,"game_id"]="second";extra.loc[:,"min"]=59
    f=make_form_frame(pd.concat([x,extra],ignore_index=True)).set_index("game_id")
    assert f.loc["g2","last_2"]==f.loc["second","last_2"]
    assert f.loc["g2","prior_games"]==f.loc["second","prior_games"]


def test_future_mutation_does_not_change_prior():
    x=sample(); a=make_form_frame(x).set_index("game_id").loc["g20","last_5"]
    x.loc[x.game_id=="g30","min"]=50
    b=make_form_frame(x).set_index("game_id").loc["g20","last_5"]
    assert a==b


def test_all_candidates_and_history():
    f=make_form_frame(sample())
    assert all(c in f for c in CANDIDATES)
    assert f.iloc[0].prior_dates==0
    assert pd.isna(f.iloc[0].last_5)
    assert f.iloc[5].last_5==pytest.approx(sample().iloc[:5]["min"].mean())
    assert len(score_forecasts(f))==len(CANDIDATES)


def test_prequential_uses_only_past():
    x=sample();a=expanding_prequential(make_form_frame(x),min_train_dates=10)
    assert len(a)>0
    x.loc[x.game_id=="g40","min"]=50
    b=expanding_prequential(make_form_frame(x),min_train_dates=10)
    assert a.loc[a.game_id=="g39",["baseline","adaptive","selected"]].equals(
        b.loc[b.game_id=="g39",["baseline","adaptive","selected"]])


def test_invalid_input():
    x=sample();x.loc[0,"min"]=-1
    with pytest.raises(ValueError):make_form_frame(x)
