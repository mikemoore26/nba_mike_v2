"""P0-S2 POC-09 — Game-Level Historical Reconstruction & Leakage Boundary.

Research only. No model training.

POC-08 proved DateTo responsiveness at day-level. POC-09 tests the safer
construction rule for a historical game on date D:

    features = season-to-date data with DateTo = D - 1 day

Then it verifies:
1. the pregame snapshot excludes the target game's contribution,
2. adding the target date changes GP for players who played,
3. player-game box scores can serve as the outcome/training target,
4. advanced/tracking pregame snapshots are retrievable using the same cutoff.

This does NOT solve intraday injury, lineup, news, or odds timestamps.
"""
from __future__ import annotations

import json, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from nba_api.stats.endpoints import (
    leaguedashplayerstats,
    leaguedashptstats,
    playergamelogs,
)

CASES = (
    ("2025-26", "11/15/2025"),
    ("2023-24", "11/15/2023"),
    ("2019-20", "11/15/2019"),
)
TRACKING = ("Possessions", "Passing", "Drives", "PaintTouch")


def jdefault(x):
    if isinstance(x, np.integer): return int(x)
    if isinstance(x, np.floating): return float(x)
    if isinstance(x, np.bool_): return bool(x)
    if isinstance(x, np.ndarray): return x.tolist()
    if pd.isna(x): return None
    raise TypeError(type(x).__name__)


def prior_day(mmddyyyy):
    d = datetime.strptime(mmddyyyy, "%m/%d/%Y").date() - timedelta(days=1)
    return d.strftime("%m/%d/%Y")


def get_agg(season, date_to, measure, timeout):
    t0=time.perf_counter()
    df=leaguedashplayerstats.LeagueDashPlayerStats(
        season=season, season_type_all_star="Regular Season",
        per_mode_detailed="Totals",
        measure_type_detailed_defense=measure,
        date_to_nullable=date_to, timeout=timeout
    ).get_data_frames()[0]
    return df, round(time.perf_counter()-t0,3)


def get_tracking(season, date_to, measure, timeout):
    t0=time.perf_counter()
    df=leaguedashptstats.LeagueDashPtStats(
        season=season, season_type_all_star="Regular Season",
        player_or_team="Player", per_mode_simple="Totals",
        pt_measure_type=measure, date_to_nullable=date_to, timeout=timeout
    ).get_data_frames()[0]
    return df, round(time.perf_counter()-t0,3)


def get_day_logs(season, game_date, timeout):
    t0=time.perf_counter()
    df=playergamelogs.PlayerGameLogs(
        season_nullable=season,
        season_type_nullable="Regular Season",
        date_from_nullable=game_date,
        date_to_nullable=game_date,
        timeout=timeout
    ).get_data_frames()[0]
    return df, round(time.perf_counter()-t0,3)


def safe(fn,*args):
    try:
        df,sec=fn(*args)
        return {"status":"PASS" if len(df) else "EMPTY","rows":int(len(df)),
                "seconds":sec,"columns":list(df.columns)},df
    except Exception as e:
        return {"status":"ERROR","exception_type":type(e).__name__,"exception":str(e)},None


def compare(pre, through, day):
    if pre is None or through is None or day is None:
        return {"status":"ERROR","reason":"one or more required frames unavailable"},None
    need={"PLAYER_ID","GP"}
    if not need.issubset(pre.columns) or not need.issubset(through.columns) or "PLAYER_ID" not in day.columns:
        return {"status":"ERROR","reason":"PLAYER_ID/GP unavailable"},None

    p=pre[["PLAYER_ID","GP"]].rename(columns={"GP":"GP_PRE"})
    t=through[["PLAYER_ID","GP"]].rename(columns={"GP":"GP_THROUGH"})
    m=p.merge(t,on="PLAYER_ID",how="outer").fillna({"GP_PRE":0,"GP_THROUGH":0})
    played=set(pd.to_numeric(day["PLAYER_ID"],errors="coerce").dropna().astype("int64"))
    m["PLAYED_TARGET_DATE"]=m["PLAYER_ID"].astype("int64").isin(played)
    m["GP_DELTA"]=pd.to_numeric(m["GP_THROUGH"])-pd.to_numeric(m["GP_PRE"])

    played_rows=m[m["PLAYED_TARGET_DATE"]]
    nonplayed_rows=m[~m["PLAYED_TARGET_DATE"]]
    played_plus_one=int((played_rows["GP_DELTA"]==1).sum())
    played_other=int((played_rows["GP_DELTA"]!=1).sum())
    nonplayed_changed=int((nonplayed_rows["GP_DELTA"]!=0).sum())
    negative=int((m["GP_DELTA"]<0).sum())

    status="PASS" if len(played_rows)>0 and played_other==0 and nonplayed_changed==0 and negative==0 else "FAIL"
    return {
        "status":status,
        "target_date_players":int(len(played_rows)),
        "target_date_players_gp_plus_one":played_plus_one,
        "target_date_players_wrong_delta":played_other,
        "non_target_players_changed":nonplayed_changed,
        "negative_gp_delta":negative,
    },m


def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--timeout",type=int,default=30)
    ap.add_argument("--sleep-seconds",type=float,default=.75)
    args=ap.parse_args()

    outdir=Path("research/p0_s2/poc09/results"); outdir.mkdir(parents=True,exist_ok=True)
    report={"poc":"P0-S2 POC-09","run_utc":datetime.now(timezone.utc).isoformat(),"results":[]}

    for season,target_date in CASES:
        cutoff=prior_day(target_date)
        r={"season":season,"target_date":target_date,"pregame_cutoff":cutoff,"tracking":{}}

        pm,pdf=safe(get_agg,season,cutoff,"Base",args.timeout); time.sleep(args.sleep_seconds)
        tm,tdf=safe(get_agg,season,target_date,"Base",args.timeout); time.sleep(args.sleep_seconds)
        gm,gdf=safe(get_day_logs,season,target_date,args.timeout)
        r["base_pregame"],r["base_through_target"],r["target_day_logs"]=pm,tm,gm

        cm,cdf=compare(pdf,tdf,gdf)
        r["leakage_boundary_test"]=cm
        if cdf is not None:
            cdf.to_csv(outdir/f"{season}_gp_boundary_comparison.csv",index=False)
        if gdf is not None:
            gdf.to_csv(outdir/f"{season}_target_day_player_games.csv",index=False)

        time.sleep(args.sleep_seconds)
        am,adf=safe(get_agg,season,cutoff,"Advanced",args.timeout)
        r["advanced_pregame"]=am
        if adf is not None: adf.head(50).to_csv(outdir/f"{season}_advanced_pregame_sample.csv",index=False)

        for measure in TRACKING:
            time.sleep(args.sleep_seconds)
            mm,mdf=safe(get_tracking,season,cutoff,measure,args.timeout)
            r["tracking"][measure]=mm
            if mdf is not None:
                mdf.head(50).to_csv(outdir/f"{season}_tracking_{measure.lower()}_pregame_sample.csv",index=False)

        core=[pm["status"],tm["status"],gm["status"],cm["status"],am["status"]]
        track=[x["status"] for x in r["tracking"].values()]
        r["status"]="PASS" if all(x=="PASS" for x in core+track) else (
            "PASS_WITH_TRACKING_GAPS" if all(x=="PASS" for x in core) else "INVESTIGATE"
        )
        report["results"].append(r)

    (outdir/"poc09_report.json").write_text(json.dumps(report,indent=2,default=jdefault),encoding="utf-8")

    lines=["P0-S2 POC-09 — Game-Level Historical Reconstruction & Leakage Boundary",
           f"Run UTC: {report['run_utc']}",""]
    for r in report["results"]:
        c=r["leakage_boundary_test"]
        lines += [
            f"Season {r['season']} | TARGET={r['target_date']} | PRE-GAME CUTOFF={r['pregame_cutoff']} | STATUS: {r['status']}",
            f"  BASE PRE: {r['base_pregame']['status']} | rows={r['base_pregame'].get('rows','n/a')} | seconds={r['base_pregame'].get('seconds','n/a')}",
            f"  BASE THROUGH TARGET: {r['base_through_target']['status']} | rows={r['base_through_target'].get('rows','n/a')} | seconds={r['base_through_target'].get('seconds','n/a')}",
            f"  TARGET DAY LOGS: {r['target_day_logs']['status']} | rows={r['target_day_logs'].get('rows','n/a')} | seconds={r['target_day_logs'].get('seconds','n/a')}",
            f"  LEAKAGE BOUNDARY: {c['status']} | target players={c.get('target_date_players','n/a')} | +1 GP={c.get('target_date_players_gp_plus_one','n/a')} | wrong target delta={c.get('target_date_players_wrong_delta','n/a')} | non-target changed={c.get('non_target_players_changed','n/a')}",
            f"  ADVANCED PRE: {r['advanced_pregame']['status']} | rows={r['advanced_pregame'].get('rows','n/a')} | seconds={r['advanced_pregame'].get('seconds','n/a')}",
        ]
        for measure,x in r["tracking"].items():
            lines.append(f"  TRACKING {measure} PRE: {x['status']} | rows={x.get('rows','n/a')} | seconds={x.get('seconds','n/a')}")
            if x.get("exception"): lines.append(f"    ERROR {x['exception_type']}: {x['exception']}")
        lines.append("")
    lines += [
        "INTERPRETATION:",
        "- PASS supports using D-1 season-to-date aggregates as leakage-safe day-level pregame features for a game on D.",
        "- Target-day player game logs are outcomes/labels, not pregame features.",
        "- This still does not solve exact intraday AS_OF_TIME for injury reports, confirmed lineups, news, or sportsbook markets.",
        "- Same-day earlier-game information is deliberately excluded by the D-1 rule; that is conservative and reproducible.",
        "- Do not train models yet.",
    ]
    summary="\n".join(lines)
    (outdir/"poc09_summary.txt").write_text(summary,encoding="utf-8")
    print(summary)

if __name__=="__main__":
    main()
