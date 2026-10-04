"""P0-S2 POC-03: PBP event ordering and substitution semantics.

Research-only. Uses representative games from POC-02 and inspects:
- actionNumber/actionId ordering
- period + clock chronology
- substitution row semantics
- same-clock/simultaneous events
- period boundaries and overtime
- whether descriptions contain enough information to identify incoming/outgoing players

This POC does NOT reconstruct rotations.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import leaguegamelog, playbyplayv3

SEASONS = ("2025-26", "2023-24", "2019-20")


def discover_game(season: str, timeout: int) -> str:
    df = leaguegamelog.LeagueGameLog(
        season=season,
        season_type_all_star="Regular Season",
        player_or_team_abbreviation="T",
        timeout=timeout,
    ).get_data_frames()[0]
    gids = sorted(df["GAME_ID"].astype(str).unique())
    if not gids:
        raise RuntimeError(f"No games discovered for {season}")
    return gids[len(gids) // 2]


def fetch_pbp(game_id: str, timeout: int) -> pd.DataFrame:
    frames = playbyplayv3.PlayByPlayV3(
        game_id=game_id,
        timeout=timeout,
    ).get_data_frames()
    if not frames:
        raise RuntimeError("No PBP frames returned")
    return frames[0].copy()


def clock_to_seconds(value: object) -> float | None:
    """Parse common NBA V3 ISO-ish clock values such as PT11M42.00S."""
    if value is None or pd.isna(value):
        return None
    text = str(value)
    m = re.fullmatch(r"PT(?:(\d+)M)?([0-9.]+)S", text)
    if m:
        minutes = int(m.group(1) or 0)
        seconds = float(m.group(2))
        return minutes * 60 + seconds
    # Fallback for MM:SS forms.
    m = re.fullmatch(r"(\d+):([0-9.]+)", text)
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    return None


def monotonic_violations(values: pd.Series) -> list[dict]:
    numeric = pd.to_numeric(values, errors="coerce")
    out = []
    prev_i = None
    prev_v = None
    for i, v in numeric.items():
        if pd.isna(v):
            continue
        if prev_v is not None and v < prev_v:
            out.append({
                "previous_row_index": int(prev_i),
                "previous_value": float(prev_v),
                "row_index": int(i),
                "value": float(v),
            })
        prev_i, prev_v = i, v
    return out


def chronology_violations(df: pd.DataFrame) -> list[dict]:
    """Within a period, game clock should generally count downward in returned order."""
    out = []
    work = df.copy()
    work["_clock_seconds"] = work["clock"].map(clock_to_seconds)
    for period, g in work.groupby("period", sort=False):
        prev_i = None
        prev_clock = None
        for i, row in g.iterrows():
            c = row["_clock_seconds"]
            if c is None or pd.isna(c):
                continue
            # Clock increasing in returned order is suspicious.
            if prev_clock is not None and c > prev_clock + 1e-9:
                out.append({
                    "period": int(period),
                    "previous_row_index": int(prev_i),
                    "previous_clock_seconds": float(prev_clock),
                    "row_index": int(i),
                    "clock_seconds": float(c),
                })
            prev_i, prev_clock = i, c
    return out


def audit(df: pd.DataFrame) -> dict:
    required = {
        "gameId", "actionNumber", "clock", "period", "teamId",
        "personId", "description", "actionType", "subType", "actionId"
    }
    missing = sorted(required - set(df.columns))
    if missing:
        return {"status": "FAIL", "missing_required_columns": missing}

    action_num_viol = monotonic_violations(df["actionNumber"])
    action_id_viol = monotonic_violations(df["actionId"])
    chrono_viol = chronology_violations(df)

    subs = df[df["actionType"].astype(str).str.lower().eq("substitution")].copy()
    same_clock_groups = (
        df.groupby(["period", "clock"], dropna=False)
        .size()
        .reset_index(name="events")
    )
    same_clock_groups = same_clock_groups[same_clock_groups["events"] > 1]

    period_rows = df[df["actionType"].astype(str).str.lower().eq("period")].copy()

    return {
        "status": "PASS",
        "rows": int(len(df)),
        "action_number_violations": len(action_num_viol),
        "action_id_violations": len(action_id_viol),
        "clock_chronology_violations": len(chrono_viol),
        "action_number_violation_examples": action_num_viol[:10],
        "action_id_violation_examples": action_id_viol[:10],
        "clock_violation_examples": chrono_viol[:10],
        "substitution_rows": int(len(subs)),
        "substitution_person_id_nulls": int(subs["personId"].isna().sum()),
        "substitution_team_id_nulls": int(subs["teamId"].isna().sum()),
        "substitution_description_nulls": int(subs["description"].isna().sum()),
        "unique_substitution_subtypes": sorted(subs["subType"].dropna().astype(str).unique().tolist()),
        "same_clock_multi_event_groups": int(len(same_clock_groups)),
        "max_events_same_period_clock": int(same_clock_groups["events"].max()) if len(same_clock_groups) else 1,
        "period_marker_rows": int(len(period_rows)),
        "periods": sorted(pd.to_numeric(df["period"], errors="coerce").dropna().astype(int).unique().tolist()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="research/p0_s2/poc03/results")
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--sleep-seconds", type=float, default=1.5)
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    report = {
        "poc": "P0-S2 POC-03",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "results": [],
    }
    failures = 0

    for season in SEASONS:
        item = {"season": season}
        try:
            gid = discover_game(season, args.timeout)
            item["game_id"] = gid
            time.sleep(args.sleep_seconds)
            t0 = time.perf_counter()
            df = fetch_pbp(gid, args.timeout)
            item["request_seconds"] = round(time.perf_counter() - t0, 3)
            item.update(audit(df))

            subs = df[df["actionType"].astype(str).str.lower().eq("substitution")].copy()
            keep = [c for c in [
                "gameId", "actionNumber", "actionId", "period", "clock",
                "teamId", "teamTricode", "personId", "playerName",
                "description", "actionType", "subType"
            ] if c in subs.columns]
            subs[keep].to_csv(out / f"{season}_{gid}_substitutions.csv", index=False)

            # Preserve contexts around first 12 substitutions.
            context_rows = []
            for idx in subs.index[:12]:
                lo = max(0, idx - 2)
                hi = min(len(df), idx + 3)
                block = df.iloc[lo:hi].copy()
                block["_sub_anchor_index"] = int(idx)
                block["_source_row_index"] = block.index
                context_rows.append(block)
            if context_rows:
                ctx = pd.concat(context_rows, ignore_index=True)
                ctx.to_csv(out / f"{season}_{gid}_substitution_context.csv", index=False)

            # Same-clock groups for manual semantics inspection.
            counts = df.groupby(["period", "clock"], dropna=False).size()
            keys = counts[counts > 1].sort_values(ascending=False).head(20).index
            chunks = []
            for period, clock in keys:
                g = df[(df["period"] == period) & (df["clock"] == clock)].copy()
                chunks.append(g)
            if chunks:
                pd.concat(chunks, ignore_index=True).to_csv(
                    out / f"{season}_{gid}_same_clock_examples.csv", index=False
                )

            if item["status"] != "PASS":
                failures += 1
        except Exception as exc:
            item.update({
                "status": "ERROR",
                "exception_type": type(exc).__name__,
                "exception": str(exc),
            })
            failures += 1

        report["results"].append(item)
        time.sleep(args.sleep_seconds)

    (out / "poc03_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    lines = [
        "P0-S2 POC-03 — PBP Event Ordering & Substitution Semantics",
        f"Run UTC: {report['run_utc']}",
        "",
    ]
    for r in report["results"]:
        lines.extend([
            f"Season {r['season']} | GAME_ID={r.get('game_id', 'n/a')}",
            f"  STATUS: {r.get('status')}",
            f"  rows={r.get('rows', 'n/a')} | seconds={r.get('request_seconds', 'n/a')}",
            f"  actionNumber reversals={r.get('action_number_violations', 'n/a')}",
            f"  actionId reversals={r.get('action_id_violations', 'n/a')}",
            f"  clock chronology violations={r.get('clock_chronology_violations', 'n/a')}",
            f"  substitutions={r.get('substitution_rows', 'n/a')}",
            f"  substitution subTypes={r.get('unique_substitution_subtypes', 'n/a')}",
            f"  same-clock multi-event groups={r.get('same_clock_multi_event_groups', 'n/a')}",
            f"  max events at same clock={r.get('max_events_same_period_clock', 'n/a')}",
            f"  periods={r.get('periods', 'n/a')}",
        ])
        if r.get("exception"):
            lines.append(f"  ERROR: {r['exception']}")
        lines.append("")

    lines.append("OVERALL SCRIPT/SCHEMA: " + ("PASS" if failures == 0 else "PARTIAL/FAIL"))
    lines.append("IMPORTANT: Interpret ordering and substitution semantics from the generated evidence before rotation reconstruction.")
    text = "\n".join(lines)
    (out / "poc03_summary.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
