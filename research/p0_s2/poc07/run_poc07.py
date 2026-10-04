"""P0-S2 POC-07 — Advanced Stats & Opportunity Data Feasibility.

Research-only probe. No model training.

Tests representative historical seasons for:
1) base player box-score opportunity fields,
2) NBA advanced player stats,
3) NBA tracking/opportunity measure types.

The purpose is source classification, not forcing every endpoint to PASS.
Timeouts/errors are recorded as feasibility evidence.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, leaguedashptstats

SEASONS = ("2025-26", "2023-24", "2019-20")

# Tracking measures deliberately cover different opportunity families.
TRACKING_MEASURES = (
    "Possessions",
    "Passing",
    "Drives",
    "PaintTouch",
)

BASE_EXPECTED = ("PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "MIN", "FGA", "FG3A", "FTA",
                 "OREB", "DREB", "REB", "AST", "TOV", "PTS")
ADV_EXPECTED = ("PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "MIN", "OFF_RATING",
                "DEF_RATING", "NET_RATING", "AST_PCT", "AST_TO", "AST_RATIO",
                "OREB_PCT", "DREB_PCT", "REB_PCT", "TM_TOV_PCT", "EFG_PCT",
                "TS_PCT", "USG_PCT", "PACE", "PIE")


def jdefault(x):
    if isinstance(x, np.integer): return int(x)
    if isinstance(x, np.floating): return float(x)
    if isinstance(x, np.bool_): return bool(x)
    if isinstance(x, np.ndarray): return x.tolist()
    if pd.isna(x): return None
    raise TypeError(type(x).__name__)


def summarize(df: pd.DataFrame, expected=()):
    present = [c for c in expected if c in df.columns]
    missing = [c for c in expected if c not in df.columns]
    null_rates = {
        c: float(df[c].isna().mean())
        for c in present
    }
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": list(df.columns),
        "expected_present": present,
        "expected_missing": missing,
        "null_rates": null_rates,
        "duplicate_full_rows": int(df.duplicated().sum()),
    }


def probe_base(season, timeout):
    t0 = time.perf_counter()
    df = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        season_type_all_star="Regular Season",
        per_mode_detailed="PerGame",
        measure_type_detailed_defense="Base",
        timeout=timeout,
    ).get_data_frames()[0]
    out = summarize(df, BASE_EXPECTED)
    out["seconds"] = round(time.perf_counter() - t0, 3)
    out["status"] = "PASS" if len(df) and not out["expected_missing"] else "PARTIAL"
    return out, df


def probe_advanced(season, timeout):
    t0 = time.perf_counter()
    df = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        season_type_all_star="Regular Season",
        per_mode_detailed="PerGame",
        measure_type_detailed_defense="Advanced",
        timeout=timeout,
    ).get_data_frames()[0]
    out = summarize(df, ADV_EXPECTED)
    out["seconds"] = round(time.perf_counter() - t0, 3)
    out["status"] = "PASS" if len(df) and not out["expected_missing"] else "PARTIAL"
    return out, df


def probe_tracking(season, measure, timeout):
    t0 = time.perf_counter()
    df = leaguedashptstats.LeagueDashPtStats(
        season=season,
        season_type_all_star="Regular Season",
        player_or_team="Player",
        per_mode_simple="PerGame",
        pt_measure_type=measure,
        timeout=timeout,
    ).get_data_frames()[0]
    out = summarize(df)
    out["seconds"] = round(time.perf_counter() - t0, 3)
    out["status"] = "PASS" if len(df) else "EMPTY"
    return out, df


def safe_probe(fn, *args):
    try:
        meta, df = fn(*args)
        return meta, df
    except Exception as exc:
        return {
            "status": "ERROR",
            "exception_type": type(exc).__name__,
            "exception": str(exc),
        }, None


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--sleep-seconds", type=float, default=1.0)
    args = ap.parse_args()

    outdir = Path("research/p0_s2/poc07/results")
    outdir.mkdir(parents=True, exist_ok=True)
    report = {
        "poc": "P0-S2 POC-07",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "results": [],
    }

    for season in SEASONS:
        s = {"season": season, "tracking": {}}

        base_meta, base_df = safe_probe(probe_base, season, args.timeout)
        s["base"] = base_meta
        if base_df is not None:
            base_df.head(50).to_csv(outdir / f"{season}_base_sample.csv", index=False)
        time.sleep(args.sleep_seconds)

        adv_meta, adv_df = safe_probe(probe_advanced, season, args.timeout)
        s["advanced"] = adv_meta
        if adv_df is not None:
            adv_df.head(50).to_csv(outdir / f"{season}_advanced_sample.csv", index=False)
        time.sleep(args.sleep_seconds)

        for measure in TRACKING_MEASURES:
            meta, df = safe_probe(probe_tracking, season, measure, args.timeout)
            s["tracking"][measure] = meta
            if df is not None:
                df.head(50).to_csv(
                    outdir / f"{season}_tracking_{measure.lower()}_sample.csv", index=False
                )
            time.sleep(args.sleep_seconds)

        statuses = [s["base"]["status"], s["advanced"]["status"]] + [
            x["status"] for x in s["tracking"].values()
        ]
        if s["base"]["status"] == "PASS" and s["advanced"]["status"] == "PASS":
            s["status"] = "PASS_WITH_TRACKING_GAPS" if any(x != "PASS" for x in statuses[2:]) else "PASS"
        elif s["base"]["status"] == "PASS":
            s["status"] = "CORE_PASS_ADVANCED_INVESTIGATE"
        else:
            s["status"] = "INVESTIGATE"

        report["results"].append(s)

    (outdir / "poc07_report.json").write_text(
        json.dumps(report, indent=2, default=jdefault), encoding="utf-8"
    )

    lines = [
        "P0-S2 POC-07 — Advanced Stats & Opportunity Data Feasibility",
        f"Run UTC: {report['run_utc']}",
        "",
    ]
    for s in report["results"]:
        lines.append(f"Season {s['season']} | STATUS: {s['status']}")
        for label in ("base", "advanced"):
            x = s[label]
            lines.append(
                f"  {label.upper()}: {x['status']} | rows={x.get('rows','n/a')} | "
                f"seconds={x.get('seconds','n/a')} | missing={x.get('expected_missing','n/a')}"
            )
            if x.get("exception"):
                lines.append(f"    ERROR {x['exception_type']}: {x['exception']}")
        for measure, x in s["tracking"].items():
            lines.append(
                f"  TRACKING {measure}: {x['status']} | rows={x.get('rows','n/a')} | "
                f"seconds={x.get('seconds','n/a')}"
            )
            if x.get("exception"):
                lines.append(f"    ERROR {x['exception_type']}: {x['exception']}")
        lines.append("")

    lines += [
        "INTERPRETATION:",
        "- Base box/opportunity fields are candidates for CORE only if historically stable.",
        "- Advanced stats are SUPPORTING candidates; availability does not prove predictive value.",
        "- Tracking fields are OPTIONAL/ADVANCED until historical depth, stability, and AS_OF_TIME-safe construction are proven.",
        "- Endpoint timeout/error is a feasibility result; do not silently replace it or call it production-ready.",
        "- This POC tests season-level access/schema, not game-by-game historical timestamp reconstruction.",
    ]
    summary = "\n".join(lines)
    (outdir / "poc07_summary.txt").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
