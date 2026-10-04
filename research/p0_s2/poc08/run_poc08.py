"""P0-S2 POC-08 — Historical Cutoff / AS_OF_TIME Feasibility.

Research-only. No model training.

Question:
Can NBA Stats season-to-date player aggregates be requested with a historical
DateTo cutoff so that NBA_MIKE can construct pregame features without using
future games from the same season?

This POC intentionally compares an EARLY cutoff with a LATER cutoff and checks
that:
- both requests return usable rows,
- GP does not decrease for matched players,
- at least some players gain games,
- aggregate values change,
- advanced and tracking endpoints also respond to the historical cutoff.

This proves cutoff responsiveness, NOT publication-time truth. Injury/news/odds
still require their own timestamped sources.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, leaguedashptstats

CASES = (
    ("2025-26", "11/15/2025", "12/15/2025"),
    ("2023-24", "11/15/2023", "12/15/2023"),
    ("2019-20", "11/15/2019", "12/15/2019"),
)

TRACKING_MEASURES = ("Possessions", "Passing", "Drives", "PaintTouch")


def jdefault(x):
    if isinstance(x, np.integer): return int(x)
    if isinstance(x, np.floating): return float(x)
    if isinstance(x, np.bool_): return bool(x)
    if isinstance(x, np.ndarray): return x.tolist()
    if pd.isna(x): return None
    raise TypeError(type(x).__name__)


def get_player_stats(season, date_to, measure, timeout):
    t0 = time.perf_counter()
    df = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        season_type_all_star="Regular Season",
        per_mode_detailed="PerGame",
        measure_type_detailed_defense=measure,
        date_to_nullable=date_to,
        timeout=timeout,
    ).get_data_frames()[0]
    return df, round(time.perf_counter() - t0, 3)


def get_tracking(season, date_to, measure, timeout):
    t0 = time.perf_counter()
    df = leaguedashptstats.LeagueDashPtStats(
        season=season,
        season_type_all_star="Regular Season",
        player_or_team="Player",
        per_mode_simple="PerGame",
        pt_measure_type=measure,
        date_to_nullable=date_to,
        timeout=timeout,
    ).get_data_frames()[0]
    return df, round(time.perf_counter() - t0, 3)


def safe(fn, *args):
    try:
        df, secs = fn(*args)
        return {"status": "PASS" if len(df) else "EMPTY", "rows": int(len(df)),
                "seconds": secs, "columns": list(df.columns)}, df
    except Exception as exc:
        return {"status": "ERROR", "exception_type": type(exc).__name__,
                "exception": str(exc)}, None


def compare_base(early, late):
    needed = {"PLAYER_ID", "PLAYER_NAME", "GP"}
    if early is None or late is None or not needed.issubset(early.columns) or not needed.issubset(late.columns):
        return {"status": "ERROR", "reason": "Required PLAYER_ID/PLAYER_NAME/GP columns unavailable"}, None

    cols = [c for c in ("PLAYER_ID","PLAYER_NAME","TEAM_ID","GP","MIN","FGA","FG3A","FTA","REB","AST","TOV","PTS")
            if c in early.columns and c in late.columns]
    a = early[cols].copy().add_suffix("_early")
    b = late[cols].copy().add_suffix("_late")
    m = a.merge(b, left_on="PLAYER_ID_early", right_on="PLAYER_ID_late", how="inner")

    gp_e = pd.to_numeric(m["GP_early"], errors="coerce")
    gp_l = pd.to_numeric(m["GP_late"], errors="coerce")
    increased = gp_l > gp_e
    decreased = gp_l < gp_e

    metric_cols = [c for c in ("MIN","FGA","FG3A","FTA","REB","AST","TOV","PTS")
                   if f"{c}_early" in m.columns and f"{c}_late" in m.columns]
    changed = pd.Series(False, index=m.index)
    for c in metric_cols:
        e = pd.to_numeric(m[f"{c}_early"], errors="coerce")
        l = pd.to_numeric(m[f"{c}_late"], errors="coerce")
        changed |= (e - l).abs() > 1e-12

    status = "PASS" if len(m) and int(increased.sum()) > 0 and int(decreased.sum()) == 0 and int(changed.sum()) > 0 else "FAIL"
    meta = {
        "status": status,
        "matched_players": int(len(m)),
        "players_gp_increased": int(increased.sum()),
        "players_gp_decreased": int(decreased.sum()),
        "players_with_changed_aggregates": int(changed.sum()),
        "metrics_compared": metric_cols,
    }
    return meta, m


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--sleep-seconds", type=float, default=0.75)
    args = ap.parse_args()

    outdir = Path("research/p0_s2/poc08/results")
    outdir.mkdir(parents=True, exist_ok=True)
    report = {"poc": "P0-S2 POC-08", "run_utc": datetime.now(timezone.utc).isoformat(), "results": []}

    for season, early_date, late_date in CASES:
        row = {"season": season, "early_date_to": early_date, "late_date_to": late_date, "tracking": {}}

        em, edf = safe(get_player_stats, season, early_date, "Base", args.timeout)
        time.sleep(args.sleep_seconds)
        lm, ldf = safe(get_player_stats, season, late_date, "Base", args.timeout)
        row["base_early"], row["base_late"] = em, lm
        cmp_meta, cmp_df = compare_base(edf, ldf)
        row["base_cutoff_comparison"] = cmp_meta
        if cmp_df is not None:
            cmp_df.to_csv(outdir / f"{season}_base_cutoff_comparison.csv", index=False)

        time.sleep(args.sleep_seconds)
        am, adf = safe(get_player_stats, season, early_date, "Advanced", args.timeout)
        row["advanced_early"] = am
        if adf is not None:
            adf.head(50).to_csv(outdir / f"{season}_advanced_early_sample.csv", index=False)

        for measure in TRACKING_MEASURES:
            time.sleep(args.sleep_seconds)
            tm, tdf = safe(get_tracking, season, early_date, measure, args.timeout)
            row["tracking"][measure] = tm
            if tdf is not None:
                tdf.head(50).to_csv(outdir / f"{season}_tracking_{measure.lower()}_early_sample.csv", index=False)

        required = [
            row["base_early"]["status"],
            row["base_late"]["status"],
            row["base_cutoff_comparison"]["status"],
            row["advanced_early"]["status"],
        ]
        tracking_status = [x["status"] for x in row["tracking"].values()]
        if all(x == "PASS" for x in required):
            row["status"] = "PASS" if all(x == "PASS" for x in tracking_status) else "PASS_WITH_TRACKING_GAPS"
        else:
            row["status"] = "INVESTIGATE"
        report["results"].append(row)

    (outdir / "poc08_report.json").write_text(
        json.dumps(report, indent=2, default=jdefault), encoding="utf-8"
    )

    lines = [
        "P0-S2 POC-08 — Historical Cutoff / AS_OF_TIME Feasibility",
        f"Run UTC: {report['run_utc']}", ""
    ]
    for r in report["results"]:
        c = r["base_cutoff_comparison"]
        lines += [
            f"Season {r['season']} | EARLY={r['early_date_to']} | LATE={r['late_date_to']} | STATUS: {r['status']}",
            f"  BASE EARLY: {r['base_early']['status']} | rows={r['base_early'].get('rows','n/a')} | seconds={r['base_early'].get('seconds','n/a')}",
            f"  BASE LATE:  {r['base_late']['status']} | rows={r['base_late'].get('rows','n/a')} | seconds={r['base_late'].get('seconds','n/a')}",
            f"  CUTOFF TEST: {c['status']} | matched={c.get('matched_players','n/a')} | GP increased={c.get('players_gp_increased','n/a')} | GP decreased={c.get('players_gp_decreased','n/a')} | aggregates changed={c.get('players_with_changed_aggregates','n/a')}",
            f"  ADVANCED EARLY: {r['advanced_early']['status']} | rows={r['advanced_early'].get('rows','n/a')} | seconds={r['advanced_early'].get('seconds','n/a')}",
        ]
        for measure, x in r["tracking"].items():
            lines.append(f"  TRACKING {measure} EARLY: {x['status']} | rows={x.get('rows','n/a')} | seconds={x.get('seconds','n/a')}")
            if x.get("exception"):
                lines.append(f"    ERROR {x['exception_type']}: {x['exception']}")
        lines.append("")

    lines += [
        "INTERPRETATION:",
        "- PASS means the season-to-date endpoint responds to a historical DateTo cutoff and the later cutoff behaves like later information.",
        "- This is necessary for leakage-safe rolling features, but it is NOT sufficient proof of exact publication-time availability.",
        "- DateTo is day-level. It does not establish intraday AS_OF_TIME truth for injuries, lineups, odds, or late-breaking news.",
        "- Advanced/tracking availability at an early cutoff makes them research candidates only; predictive value remains unproven.",
        "- Do not train models yet.",
    ]
    summary = "\n".join(lines)
    (outdir / "poc08_summary.txt").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
