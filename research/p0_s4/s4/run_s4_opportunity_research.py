"""Descriptive, date-safe opportunity research; requires nba_api network access."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from nba_mike.features.opportunity import build_opportunity_research_frame

SEASONS=("2019-20","2023-24","2025-26")
OUT=Path("research/p0_s4/s4/results")
OUT.mkdir(parents=True,exist_ok=True)
SIGNALS=("prior_minutes","minutes_last3_avg","minutes_last5_avg","minutes_last10_avg","minutes_season_avg")
LABELS=("prior_minutes_mae","last3_mae","last5_mae","last10_mae","season_avg_mae")

def fetch(season):
    from nba_api.stats.endpoints import playergamelogs
    raw=playergamelogs.PlayerGameLogs(season_nullable=season,season_type_nullable="Regular Season",timeout=90).get_data_frames()[0]
    ren={"GAME_ID":"game_id","GAME_DATE":"event_date","PLAYER_ID":"player_id","TEAM_ID":"team_id",
         "MIN":"min","PTS":"pts","REB":"reb","AST":"ast","FG3M":"fg3m"}
    return raw.rename(columns=ren)[list(ren.values())]

def metrics(df):
    result={"rows":int(len(df))}
    for signal,label in zip(SIGNALS,LABELS):
        valid=df.dropna(subset=[signal,"target_minutes"])
        result[label]=None if valid.empty else float(np.mean(np.abs(valid["target_minutes"]-valid[signal])))
        result[label.replace("_mae","_n")]=int(len(valid))
    return result

def analyze(frame):
    frame=frame.copy()
    frame["history_group"]=pd.cut(frame.prior_games,[-1,0,2,4,9,np.inf],
                                   labels=["0","1-2","3-4","5-9","10+"])
    frame["minutes_group"]=pd.cut(frame.target_minutes,[-0.001,10,20,30,60],
                                   labels=["0-10","10-20","20-30","30-60"])
    groups={"overall_5plus":frame[frame.prior_games>=5],
            "stable_5plus":frame[(frame.prior_games>=5)&(frame.minutes_role_change_flag==0)],
            "role_change_5plus":frame[(frame.prior_games>=5)&(frame.minutes_role_change_flag==1)]}
    for name in frame.history_group.cat.categories:
        groups[f"history_{name}"]=frame[frame.history_group==name]
    for name in frame.minutes_group.cat.categories:
        groups[f"realized_minutes_{name}_5plus"]=frame[(frame.minutes_group==name)&(frame.prior_games>=5)]
    return {k:metrics(v) for k,v in groups.items()}

def main():
    report={"method":"calendar-date D-1, prior-only descriptive MAE","seasons":{}}
    flat=[]
    for season in SEASONS:
        frame=build_opportunity_research_frame(fetch(season))
        grouped=analyze(frame)
        report["seasons"][season]={"source_rows":int(len(frame)),"groups":grouped}
        for group,m in grouped.items(): flat.append({"season":season,"group":group,**m})
        overall=grouped["overall_5plus"]
        best=min((k for k in LABELS if overall[k] is not None),key=lambda k:overall[k])
        print(f"{season}: {overall['rows']} eligible; best {best}={overall[best]:.4f}; role-change {grouped['role_change_5plus']['rows']}")
    report["limitations"]=[
        "MAE is descriptive, not a production or betting validation",
        "Role-change threshold of 6 minutes is heuristic",
        "Realized-minutes buckets are retrospective diagnostics, not pregame segments",
        "Multiple games on the same date are grouped for historical features; this differs from a rolling game count",
        "Season-specific runs avoid crossing season boundaries",
        "Unobserved DNPs are not reconstructed by PlayerGameLogs",
    ]
    (OUT/"s4_1_opportunity_research.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    pd.DataFrame(flat).to_csv(OUT/"s4_1_opportunity_groups.csv",index=False)
    print("S4.1 RESEARCH COMPLETE; original S4 results preserved")
if __name__=="__main__": main()
