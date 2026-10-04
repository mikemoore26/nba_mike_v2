"""P0-S2 POC-06 — Official GameRotation/Stint Feasibility Truth Test.

Research only. Tests NBA Stats GameRotation across three eras and validates
stint-derived minutes against official traditional box-score minutes.

Important: GameRotation time values are treated empirically. The script tests
candidate scale factors against official player minutes instead of silently
assuming units.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from nba_api.stats.endpoints import (
    boxscoretraditionalv3,
    gamerotation,
    leaguegamelog,
)

SEASONS = ("2025-26", "2023-24", "2019-20")
SCALE_CANDIDATES = (1.0, 10.0, 100.0, 1000.0)


def json_default(x):
    if isinstance(x, np.integer): return int(x)
    if isinstance(x, np.floating): return float(x)
    if isinstance(x, np.bool_): return bool(x)
    if isinstance(x, np.ndarray): return x.tolist()
    if pd.isna(x): return None
    raise TypeError(type(x).__name__)


def discover_game(season, timeout=30):
    df = leaguegamelog.LeagueGameLog(
        season=season, season_type_all_star="Regular Season",
        player_or_team_abbreviation="T", timeout=timeout
    ).get_data_frames()[0]
    ids = sorted(df["GAME_ID"].astype(str).unique())
    return ids[len(ids)//2]


def get_player_box(game_id, timeout=30):
    frames = boxscoretraditionalv3.BoxScoreTraditionalV3(
        game_id=game_id, timeout=timeout
    ).get_data_frames()
    for df in frames:
        if ("personId" in df.columns or "PLAYER_ID" in df.columns) and (
            "minutes" in df.columns or "MIN" in df.columns
        ):
            return df.copy()
    raise RuntimeError("player box frame not found")


def parse_minutes(v):
    if v is None or pd.isna(v): return 0.0
    s = str(v).strip()
    if not s: return 0.0
    if s.startswith("PT") and s.endswith("S"):
        s2 = s[2:-1]
        if "M" in s2:
            m, sec = s2.split("M", 1)
            return float(m or 0) + float(sec or 0)/60
        return float(s2)/60
    if ":" in s:
        m, sec = s.split(":", 1)
        return float(m) + float(sec)/60
    return float(s)


def standard_box(box):
    pid = "personId" if "personId" in box.columns else "PLAYER_ID"
    tid = "teamId" if "teamId" in box.columns else "TEAM_ID"
    mn = "minutes" if "minutes" in box.columns else "MIN"
    if "name" in box.columns:
        names = box["name"].astype(str)
    elif "playerName" in box.columns:
        names = box["playerName"].astype(str)
    elif "PLAYER_NAME" in box.columns:
        names = box["PLAYER_NAME"].astype(str)
    elif "firstName" in box.columns and "familyName" in box.columns:
        names = box["firstName"].astype(str) + " " + box["familyName"].astype(str)
    else:
        names = box[pid].astype(str)
    return pd.DataFrame({
        "player_id": pd.to_numeric(box[pid], errors="coerce"),
        "team_id": pd.to_numeric(box[tid], errors="coerce"),
        "player_name": names,
        "official_minutes": box[mn].map(parse_minutes),
    }).dropna(subset=["player_id", "team_id"])


def rotation_frame(game_id, timeout=30):
    obj = gamerotation.GameRotation(game_id=game_id, timeout=timeout)
    frames = obj.get_data_frames()
    if len(frames) < 2:
        raise RuntimeError(f"GameRotation returned {len(frames)} frames")
    parts = []
    for label, df in zip(("away", "home"), frames[:2]):
        x = df.copy()
        x["SIDE"] = label
        parts.append(x)
    return pd.concat(parts, ignore_index=True)


def evaluate_scale(rot, box, scale):
    x = rot.copy()
    x["IN_TIME_REAL"] = pd.to_numeric(x["IN_TIME_REAL"], errors="coerce")
    x["OUT_TIME_REAL"] = pd.to_numeric(x["OUT_TIME_REAL"], errors="coerce")
    x["stint_minutes"] = (x["OUT_TIME_REAL"] - x["IN_TIME_REAL"]) / scale / 60.0
    mins = x.groupby(["PERSON_ID", "TEAM_ID"], as_index=False)["stint_minutes"].sum()
    mins = mins.rename(columns={"PERSON_ID":"player_id", "TEAM_ID":"team_id"})
    comp = box.merge(mins, on=["player_id","team_id"], how="left")
    comp["stint_minutes"] = comp["stint_minutes"].fillna(0.0)
    comp["minute_error"] = comp["stint_minutes"] - comp["official_minutes"]
    comp["abs_minute_error"] = comp["minute_error"].abs()
    played = comp[comp["official_minutes"] > 0]
    return {
        "scale": scale,
        "mae": float(played["abs_minute_error"].mean()) if len(played) else None,
        "max_abs_error": float(played["abs_minute_error"].max()) if len(played) else None,
        "players_gt_0_25": int((played["abs_minute_error"] > .25).sum()),
        "comparison": comp,
    }


def lineup_integrity(rot, scale):
    """Check active-player counts at every stint boundary midpoint."""
    findings = []
    for team_id, tdf in rot.groupby("TEAM_ID"):
        starts = pd.to_numeric(tdf["IN_TIME_REAL"], errors="coerce") / scale
        ends = pd.to_numeric(tdf["OUT_TIME_REAL"], errors="coerce") / scale
        pids = pd.to_numeric(tdf["PERSON_ID"], errors="coerce")
        bounds = sorted(set(starts.dropna()) | set(ends.dropna()))
        bad = []
        for a, b in zip(bounds[:-1], bounds[1:]):
            if b <= a: continue
            mid = (a+b)/2
            active = set(pids[(starts <= mid) & (ends > mid)].dropna().astype(int))
            if len(active) != 5:
                bad.append({"start_seconds":a, "end_seconds":b, "active_count":len(active)})
        findings.append({
            "team_id": int(team_id),
            "boundary_intervals": max(0, len(bounds)-1),
            "bad_active_count_intervals": len(bad),
            "bad_examples": bad[:10],
        })
    return findings


def main():
    out = Path("research/p0_s2/poc06/results")
    out.mkdir(parents=True, exist_ok=True)
    report = {"poc":"P0-S2 POC-06", "run_utc":datetime.now(timezone.utc).isoformat(), "results":[]}

    for season in SEASONS:
        r = {"season":season}
        try:
            gid = discover_game(season)
            r["game_id"] = gid
            time.sleep(1.0)
            rot = rotation_frame(gid)
            time.sleep(1.0)
            box = standard_box(get_player_box(gid))

            r["rotation_rows"] = int(len(rot))
            r["rotation_columns"] = list(rot.columns)
            r["null_rates"] = {
                c: float(rot[c].isna().mean())
                for c in ("PERSON_ID","TEAM_ID","IN_TIME_REAL","OUT_TIME_REAL")
                if c in rot.columns
            }
            r["duplicate_rows"] = int(rot.duplicated().sum())
            r["teams"] = int(rot["TEAM_ID"].nunique()) if "TEAM_ID" in rot.columns else None
            r["players"] = int(rot["PERSON_ID"].nunique()) if "PERSON_ID" in rot.columns else None

            evals = [evaluate_scale(rot, box, s) for s in SCALE_CANDIDATES]
            best = min(evals, key=lambda z: float("inf") if z["mae"] is None else z["mae"])
            r["scale_trials"] = [
                {k:v for k,v in e.items() if k != "comparison"} for e in evals
            ]
            r["best_time_scale_divisor"] = best["scale"]
            r["mae_minutes"] = best["mae"]
            r["max_abs_error_minutes"] = best["max_abs_error"]
            r["players_gt_0_25_min_error"] = best["players_gt_0_25"]
            r["lineup_integrity"] = lineup_integrity(rot, best["scale"])

            best["comparison"].to_csv(
                out / f"{season}_{gid}_rotation_minute_comparison.csv", index=False
            )
            rot.to_csv(out / f"{season}_{gid}_rotation_raw.csv", index=False)

            critical_cols = {"PERSON_ID","TEAM_ID","IN_TIME_REAL","OUT_TIME_REAL"}
            schema_ok = critical_cols.issubset(rot.columns)
            no_nulls = all(r["null_rates"].get(c, 1.0) == 0 for c in critical_cols)
            minute_ok = best["max_abs_error"] is not None and best["max_abs_error"] <= 0.25
            lineup_ok = all(x["bad_active_count_intervals"] == 0 for x in r["lineup_integrity"])
            r["status"] = "PASS" if schema_ok and no_nulls and minute_ok and lineup_ok else "INVESTIGATE"

        except Exception as exc:
            r["status"] = "ERROR"
            r["exception_type"] = type(exc).__name__
            r["exception"] = str(exc)
        report["results"].append(r)
        time.sleep(1.0)

    (out/"poc06_report.json").write_text(
        json.dumps(report, indent=2, default=json_default), encoding="utf-8"
    )

    lines = [
        "P0-S2 POC-06 — Official GameRotation/Stint Feasibility Truth Test",
        f"Run UTC: {report['run_utc']}", ""
    ]
    for r in report["results"]:
        lines += [
            f"Season {r['season']} | GAME_ID={r.get('game_id','n/a')}",
            f"  STATUS: {r['status']}",
            f"  rotation rows={r.get('rotation_rows','n/a')} | players={r.get('players','n/a')} | teams={r.get('teams','n/a')}",
            f"  best time scale divisor={r.get('best_time_scale_divisor','n/a')}",
            f"  MAE minutes={r.get('mae_minutes','n/a')}",
            f"  max abs error minutes={r.get('max_abs_error_minutes','n/a')}",
            f"  players >0.25 min error={r.get('players_gt_0_25_min_error','n/a')}",
        ]
        for li in r.get("lineup_integrity", []):
            lines.append(
                f"  TEAM {li['team_id']}: intervals={li['boundary_intervals']} | "
                f"non-5-player intervals={li['bad_active_count_intervals']}"
            )
        if r.get("exception"):
            lines.append(f"  ERROR {r['exception_type']}: {r['exception']}")
        lines.append("")
    lines += [
        "INTERPRETATION:",
        "PASS means GameRotation produced structurally valid stint data whose derived minutes reproduce official box-score minutes within the strict tolerance for the tested game.",
        "A PASS is feasibility evidence only; broader sampled validation is still required before production use."
    ]
    summary = "\n".join(lines)
    (out/"poc06_summary.txt").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
