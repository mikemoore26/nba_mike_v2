"""Leakage-safe descriptive minutes and opportunity research."""
from __future__ import annotations
import numpy as np
import pandas as pd

class OpportunityFeatureError(ValueError):
    pass

REQ=("game_id","event_date","player_id","team_id","min","pts","reb","ast","fg3m")
STATS=("min","pts","reb","ast","fg3m")

def build_opportunity_research_frame(df: pd.DataFrame) -> pd.DataFrame:
    missing=[c for c in REQ if c not in df.columns]
    if missing: raise OpportunityFeatureError(f"missing required columns: {missing}")
    x=df.loc[:,REQ].copy()
    x["event_date"]=pd.to_datetime(x["event_date"],errors="coerce")
    if x["event_date"].isna().any(): raise OpportunityFeatureError("invalid event_date")
    # A target-date feature may only see observations strictly before its calendar date.
    x["event_date"]=x["event_date"].dt.normalize()
    if x.duplicated(["game_id","player_id"]).any(): raise OpportunityFeatureError("duplicate player-game")
    for c in STATS: x[c]=pd.to_numeric(x[c],errors="coerce")
    if x[list(STATS)].isna().any().any() or not np.isfinite(x[list(STATS)].to_numpy(dtype=float)).all():
        raise OpportunityFeatureError("missing or nonfinite realized statistics")
    if (x["min"]<0).any() or (x["min"]>60).any():
        raise OpportunityFeatureError("invalid minutes")
    if (x[["pts","reb","ast","fg3m"]]<0).any().any():
        raise OpportunityFeatureError("negative counting statistics")
    x=x.sort_values(["player_id","event_date","game_id"],kind="stable").reset_index(drop=True)
    # Build one row per player/date of available PRIOR outcomes. Multiple
    # games on a date must not be used to predict one another.
    day=x.groupby(["player_id","event_date"],sort=False).agg(
        games_on_date=("game_id","size"),
        min=("min","mean"),
        pts=("pts","mean"),reb=("reb","mean"),ast=("ast","mean"),fg3m=("fg3m","mean"),
    ).reset_index()
    day=day.sort_values(["player_id","event_date"],kind="stable").reset_index(drop=True)
    g=day.groupby("player_id",sort=False)
    # prior_games is actual prior game count, not prior distinct dates
    day["prior_games"]=(g["games_on_date"].cumsum()-day["games_on_date"]).astype(int)
    day["prior_minutes"]=g["min"].shift(1)
    for w in (3,5,10):
        day[f"minutes_last{w}_avg"]=g["min"].transform(lambda s:s.shift(1).rolling(w,min_periods=1).mean())
        day[f"minutes_last{w}_std"]=g["min"].transform(lambda s:s.shift(1).rolling(w,min_periods=2).std(ddof=0))
    day["minutes_season_avg"]=g["min"].transform(lambda s:s.shift(1).expanding(min_periods=1).mean())
    day["minutes_season_std"]=g["min"].transform(lambda s:s.shift(1).expanding(min_periods=2).std(ddof=0))
    day["minutes_role_delta_3_vs_season"]=day["minutes_last3_avg"]-day["minutes_season_avg"]
    day["minutes_role_change_flag"]=(day["minutes_role_delta_3_vs_season"].abs()>=6).astype("int8")
    denom=day["min"].replace(0,np.nan)
    for stat in ("pts","reb","ast","fg3m"):
        rate=day[stat]/denom
        day[f"{stat}_per_min_last5"]=rate.groupby(day["player_id"]).transform(
            lambda s:s.shift(1).rolling(5,min_periods=1).mean()
        )
    derived=day.drop(columns=["games_on_date",*STATS])
    result=x.merge(derived,on=["player_id","event_date"],how="left",validate="many_to_one")
    result["target_minutes"]=result["min"]
    return result.drop(columns=list(STATS)).reset_index(drop=True)
