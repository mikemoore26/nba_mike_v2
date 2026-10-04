"""P0-S2 POC-02: Play-by-play, substitutions, and rotation feasibility.

Research-only. Uses one representative regular-season game from each target
season, discovered from LeagueGameLog, then probes PlayByPlayV3.
"""
from __future__ import annotations
import argparse, json, time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import leaguegamelog, playbyplayv3

SEASONS=("2025-26","2023-24","2019-20")

def discover_game(season:str, timeout:int)->str:
    df=leaguegamelog.LeagueGameLog(
        season=season, season_type_all_star="Regular Season",
        player_or_team_abbreviation="T", timeout=timeout
    ).get_data_frames()[0]
    if df.empty:
        raise RuntimeError(f"No team game logs for {season}")
    # pick a game away from the first/last edge of season when possible
    gids=sorted(df["GAME_ID"].astype(str).unique())
    return gids[len(gids)//2]

def fetch_pbp(game_id:str, timeout:int)->pd.DataFrame:
    frames=playbyplayv3.PlayByPlayV3(game_id=game_id, timeout=timeout).get_data_frames()
    # Action list is normally first frame.
    if not frames:
        raise RuntimeError("No data frames returned")
    return frames[0]

def first_present(cols, candidates):
    for c in candidates:
        if c in cols:
            return c
    return None

def audit(df:pd.DataFrame)->dict:
    cols=list(df.columns)
    action_col=first_present(cols,["actionType","ACTION_TYPE","action_type"])
    sub_col=first_present(cols,["subType","SUB_TYPE","sub_type"])
    period_col=first_present(cols,["period","PERIOD"])
    clock_col=first_present(cols,["clock","PCTIMESTRING","CLOCK"])
    order_col=first_present(cols,["actionNumber","ACTION_NUMBER","orderNumber","ORDER_NUMBER"])
    person_col=first_present(cols,["personId","PERSON_ID","player1_id","PLAYER1_ID"])
    score_home=first_present(cols,["scoreHome","SCORE_HOME"])
    score_away=first_present(cols,["scoreAway","SCORE_AWAY"])

    result={
        "rows":int(len(df)),
        "columns":len(cols),
        "column_names":cols,
        "action_column":action_col,
        "subtype_column":sub_col,
        "period_column":period_col,
        "clock_column":clock_col,
        "order_column":order_col,
        "person_id_column":person_col,
        "score_home_column":score_home,
        "score_away_column":score_away,
        "duplicate_full_rows":int(df.duplicated().sum()) if len(df) else 0,
    }

    if action_col:
        s=df[action_col].astype(str).str.lower()
        result["substitution_rows"]=int(s.str.contains("substitution|sub").sum())
        result["action_types_sample"]=sorted(df[action_col].dropna().astype(str).unique().tolist())[:50]
    else:
        result["substitution_rows"]=None

    if period_col:
        result["periods"]=sorted(pd.to_numeric(df[period_col],errors="coerce").dropna().astype(int).unique().tolist())
    if person_col:
        result["person_id_null_rate"]=float(df[person_col].isna().mean()) if len(df) else None
        result["unique_person_ids"]=int(df[person_col].dropna().nunique())
    if order_col and len(df):
        vals=pd.to_numeric(df[order_col],errors="coerce").dropna()
        result["order_monotonic_increasing"]=bool(vals.is_monotonic_increasing) if len(vals) else None

    essentials=[period_col,clock_col,action_col]
    result["status"]="PASS" if len(df)>0 and all(essentials) else "FAIL"
    return result

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="research/p0_s2/poc02/results")
    ap.add_argument("--timeout",type=int,default=30)
    ap.add_argument("--sleep-seconds",type=float,default=1.5)
    args=ap.parse_args()
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)

    report={"poc":"P0-S2 POC-02","run_utc":datetime.now(timezone.utc).isoformat(),"results":[]}
    failures=0

    for season in SEASONS:
        item={"season":season}
        try:
            gid=discover_game(season,args.timeout)
            item["game_id"]=gid
            time.sleep(args.sleep_seconds)
            t=time.perf_counter()
            df=fetch_pbp(gid,args.timeout)
            item["request_seconds"]=round(time.perf_counter()-t,3)
            item.update(audit(df))
            # preserve small evidence
            df.head(50).to_csv(out/f"{season}_{gid}_pbp_sample.csv",index=False)
            (out/f"{season}_{gid}_schema.json").write_text(
                json.dumps({"columns":list(df.columns),"dtypes":{c:str(t) for c,t in df.dtypes.items()}},indent=2),
                encoding="utf-8"
            )
            if item["status"]!="PASS": failures+=1
        except Exception as exc:
            item.update({"status":"ERROR","exception_type":type(exc).__name__,"exception":str(exc)})
            failures+=1
        report["results"].append(item)
        time.sleep(args.sleep_seconds)

    (out/"poc02_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")

    lines=["P0-S2 POC-02 — Play-by-Play & Rotation Feasibility",f"Run UTC: {report['run_utc']}",""]
    for r in report["results"]:
        lines += [
            f"Season {r['season']} | GAME_ID={r.get('game_id','n/a')}",
            f"  STATUS: {r.get('status')}",
            f"  rows={r.get('rows','n/a')} | seconds={r.get('request_seconds','n/a')}",
            f"  period={r.get('period_column')} | clock={r.get('clock_column')} | action={r.get('action_column')}",
            f"  person_id={r.get('person_id_column')} | substitutions={r.get('substitution_rows','n/a')}",
            f"  score_home={r.get('score_home_column')} | score_away={r.get('score_away_column')}",
        ]
        if r.get("exception"): lines.append(f"  ERROR: {r['exception']}")
        lines.append("")
    lines.append("OVERALL: "+("PASS" if failures==0 else "PARTIAL/FAIL"))
    lines.append("NOTE: PBP access does not by itself prove reliable lineup reconstruction.")
    text="\n".join(lines)
    (out/"poc02_summary.txt").write_text(text,encoding="utf-8")
    print(text)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
