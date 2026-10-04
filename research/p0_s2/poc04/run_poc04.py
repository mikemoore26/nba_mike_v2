"""P0-S2 POC-04 — Rotation Reconstruction Truth Test.

Research-only. Reconstructs on-court player intervals from NBA play-by-play
substitutions, resolves incoming-player names against the official game box
score, and compares reconstructed minutes with official minutes.

This is deliberately a feasibility/truth test, not production rotation code.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import time
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import numpy as np
from nba_api.stats.endpoints import (
    boxscoretraditionalv3,
    leaguegamelog,
    playbyplayv3,
)

SEASONS = ("2025-26", "2023-24", "2019-20")


def json_default(value):
    """Convert pandas/numpy scalar values to standard JSON-compatible Python types."""
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if pd.isna(value):
        return None
    raise TypeError(
        f"Object of type {value.__class__.__name__} is not JSON serializable"
    )


def discover_game(season: str, timeout: int) -> str:
    df = leaguegamelog.LeagueGameLog(
        season=season,
        season_type_all_star="Regular Season",
        player_or_team_abbreviation="T",
        timeout=timeout,
    ).get_data_frames()[0]
    gids = sorted(df["GAME_ID"].astype(str).unique())
    if not gids:
        raise RuntimeError(f"No games found for {season}")
    return gids[len(gids) // 2]


def fetch_pbp(game_id: str, timeout: int) -> pd.DataFrame:
    frames = playbyplayv3.PlayByPlayV3(
        game_id=game_id, timeout=timeout
    ).get_data_frames()
    if not frames:
        raise RuntimeError("No PBP frame returned")
    return frames[0].copy()


def fetch_box(game_id: str, timeout: int) -> pd.DataFrame:
    frames = boxscoretraditionalv3.BoxScoreTraditionalV3(
        game_id=game_id, timeout=timeout
    ).get_data_frames()
    if not frames:
        raise RuntimeError("No box-score frames returned")

    # Find the frame that actually contains player rows.
    for df in frames:
        cols = set(df.columns)
        if (
            ("personId" in cols or "person_id" in cols)
            and ("minutes" in cols or "MIN" in cols)
        ):
            return df.copy()
    raise RuntimeError(
        "Could not identify player box-score frame. "
        f"Frame schemas: {[list(x.columns) for x in frames]}"
    )


def col(df: pd.DataFrame, *names: str) -> str:
    for name in names:
        if name in df.columns:
            return name
    raise KeyError(f"None of these columns exist: {names}")


def clock_to_seconds(value: object) -> float:
    text = str(value)
    m = re.fullmatch(r"PT(?:(\d+)M)?([0-9.]+)S", text)
    if m:
        return int(m.group(1) or 0) * 60 + float(m.group(2))
    m = re.fullmatch(r"(\d+):([0-9.]+)", text)
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    raise ValueError(f"Unsupported clock: {value!r}")


def period_length(period: int) -> float:
    return 720.0 if period <= 4 else 300.0


def elapsed_game_seconds(period: int, clock: object) -> float:
    before = 0.0
    for p in range(1, period):
        before += period_length(p)
    return before + (period_length(period) - clock_to_seconds(clock))


def normalize_name(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("’", "'")
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    # Suffixes often vary between feeds/descriptions.
    tokens = [t for t in text.split() if t not in {"jr", "sr", "ii", "iii", "iv"}]
    return " ".join(tokens)


def parse_minutes(value: object) -> float:
    if value is None or pd.isna(value):
        return 0.0
    text = str(value).strip()
    if not text:
        return 0.0
    # V3 commonly uses ISO duration, but tolerate MM:SS and numeric minutes.
    m = re.fullmatch(r"PT(?:(\d+)M)?([0-9.]+)S", text)
    if m:
        return int(m.group(1) or 0) + float(m.group(2)) / 60.0
    m = re.fullmatch(r"(\d+):([0-9.]+)", text)
    if m:
        return int(m.group(1)) + float(m.group(2)) / 60.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def build_roster(box: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    pid = col(box, "personId", "person_id", "PLAYER_ID")
    team = col(box, "teamId", "team_id", "TEAM_ID")
    minutes = col(box, "minutes", "MIN")
    first = next((x for x in ("firstName", "first_name") if x in box.columns), None)
    family = next((x for x in ("familyName", "family_name") if x in box.columns), None)
    display = next(
        (x for x in ("name", "playerName", "PLAYER_NAME") if x in box.columns),
        None,
    )

    rows = []
    for _, r in box.iterrows():
        if pd.isna(r[pid]) or pd.isna(r[team]):
            continue
        if display:
            name = str(r[display])
        elif first and family:
            name = f"{r[first]} {r[family]}".strip()
        else:
            name = str(r[pid])

        rows.append(
            {
                "player_id": int(r[pid]),
                "team_id": int(r[team]),
                "player_name": name,
                "normalized_name": normalize_name(name),
                "official_minutes": parse_minutes(r[minutes]),
            }
        )

    roster = pd.DataFrame(rows)
    lookup: dict[int, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for rec in roster.to_dict("records"):
        lookup[rec["team_id"]][rec["normalized_name"]].append(rec)
        # Also allow unique surname matching as fallback.
        surname = rec["normalized_name"].split()[-1] if rec["normalized_name"] else ""
        if surname:
            lookup[rec["team_id"]][surname].append(rec)
    return roster, lookup


def resolve_incoming(
    incoming_text: str, team_id: int, lookup: dict
) -> tuple[int | None, str]:
    norm = normalize_name(incoming_text)
    candidates = lookup.get(team_id, {}).get(norm, [])
    unique = {c["player_id"]: c for c in candidates}
    if len(unique) == 1:
        return next(iter(unique)), "exact_or_unique_normalized"

    # Descriptions commonly use surname only.
    surname = norm.split()[-1] if norm else ""
    candidates = lookup.get(team_id, {}).get(surname, [])
    unique = {c["player_id"]: c for c in candidates}
    if len(unique) == 1:
        return next(iter(unique)), "unique_surname"

    return None, "unresolved_or_ambiguous"


def parse_incoming(description: object) -> str | None:
    m = re.match(r"SUB:\s*(.+?)\s+FOR\s+(.+?)\s*$", str(description), flags=re.I)
    return m.group(1).strip() if m else None


def infer_period_starters(
    events: pd.DataFrame,
    roster: pd.DataFrame,
    team_id: int,
    period: int,
) -> tuple[set[int], dict]:
    """Infer period starters by walking backward from first substitution.

    Before a team's first substitution in a period, every outgoing player must
    have been on court. Other players observed in basketball actions before that
    substitution are starter candidates. We accept only a uniquely determined
    five-player set; otherwise reconstruction is flagged rather than guessed.
    """
    g = events[(events["_team_id"] == team_id) & (events["_period"] == period)].copy()
    if g.empty:
        return set(), {"status": "NO_TEAM_EVENTS"}

    subs = g[g["_action_type"].eq("substitution")]
    first_sub_elapsed = float(subs["_elapsed"].min()) if len(subs) else math.inf
    pre = g[g["_elapsed"] <= first_sub_elapsed].copy()

    candidates: set[int] = set()
    outgoing: set[int] = set()

    for _, r in pre.iterrows():
        pid = r["_person_id"]
        if pd.isna(pid):
            continue
        pid = int(pid)
        if pid not in set(roster[roster["team_id"] == team_id]["player_id"]):
            continue
        action = r["_action_type"]
        if action == "substitution":
            outgoing.add(pid)
            candidates.add(pid)
        elif action not in {"timeout", "period", "instant replay"}:
            candidates.add(pid)

    # Outgoing players at the first substitution timestamp are definitely on court.
    if len(subs):
        t = float(subs["_elapsed"].min())
        first_subs = subs[subs["_elapsed"] == t]
        outgoing |= set(first_subs["_person_id"].dropna().astype(int).tolist())
        candidates |= outgoing

    info = {
        "candidate_count": len(candidates),
        "outgoing_at_first_sub_count": len(outgoing),
        "candidates": sorted(candidates),
    }
    if len(candidates) == 5:
        info["status"] = "UNIQUE_FIVE"
        return candidates, info

    info["status"] = "AMBIGUOUS"
    return set(), info


def reconstruct(
    pbp: pd.DataFrame, roster: pd.DataFrame, lookup: dict
) -> tuple[pd.DataFrame, dict]:
    action = col(pbp, "actionType", "ACTION_TYPE")
    period_c = col(pbp, "period", "PERIOD")
    clock_c = col(pbp, "clock", "CLOCK", "PCTIMESTRING")
    team_c = col(pbp, "teamId", "TEAM_ID")
    person_c = col(pbp, "personId", "PERSON_ID")
    desc_c = col(pbp, "description", "DESCRIPTION")
    aid_c = col(pbp, "actionId", "ACTION_ID")

    work = pbp.copy()
    work["_action_type"] = work[action].astype(str).str.lower()
    work["_period"] = pd.to_numeric(work[period_c], errors="coerce").astype("Int64")
    work["_team_id"] = pd.to_numeric(work[team_c], errors="coerce").astype("Int64")
    work["_person_id"] = pd.to_numeric(work[person_c], errors="coerce").astype("Int64")
    work["_action_id"] = pd.to_numeric(work[aid_c], errors="coerce")
    work["_elapsed"] = [
        elapsed_game_seconds(int(p), c)
        for p, c in zip(work["_period"], work[clock_c])
    ]
    work["_description"] = work[desc_c].astype(str)

    max_period = int(work["_period"].max())
    game_seconds = sum(period_length(p) for p in range(1, max_period + 1))
    teams = sorted(roster["team_id"].unique().tolist())

    seconds = defaultdict(float)
    errors = []
    resolutions = []
    period_starter_info = []

    for period in range(1, max_period + 1):
        period_start = sum(period_length(p) for p in range(1, period))
        period_end = period_start + period_length(period)

        lineups: dict[int, set[int]] = {}
        last_time: dict[int, float] = {}

        for team_id in teams:
            starters, info = infer_period_starters(work, roster, team_id, period)
            info.update({"period": period, "team_id": int(team_id)})
            period_starter_info.append(info)
            lineups[int(team_id)] = set(starters)
            last_time[int(team_id)] = period_start
            if len(starters) != 5:
                errors.append(
                    {
                        "type": "STARTER_INFERENCE_FAILED",
                        "period": period,
                        "team_id": int(team_id),
                        "details": info,
                    }
                )

        period_events = work[work["_period"] == period].sort_values(
            ["_elapsed", "_action_id"], kind="stable"
        )

        for _, r in period_events.iterrows():
            if r["_action_type"] != "substitution" or pd.isna(r["_team_id"]):
                continue
            team_id = int(r["_team_id"])
            if team_id not in lineups or len(lineups[team_id]) != 5:
                continue

            t = float(r["_elapsed"])
            delta = max(0.0, t - last_time[team_id])
            for pid in lineups[team_id]:
                seconds[pid] += delta
            last_time[team_id] = t

            if pd.isna(r["_person_id"]):
                errors.append({"type": "MISSING_OUTGOING_ID", "period": period, "team_id": team_id})
                continue

            outgoing = int(r["_person_id"])
            incoming_text = parse_incoming(r["_description"])
            incoming, method = (
                resolve_incoming(incoming_text, team_id, lookup)
                if incoming_text
                else (None, "description_parse_failed")
            )
            resolutions.append(
                {
                    "period": period,
                    "elapsed": t,
                    "team_id": team_id,
                    "outgoing_id": outgoing,
                    "incoming_text": incoming_text,
                    "incoming_id": incoming,
                    "resolution_method": method,
                }
            )

            if outgoing not in lineups[team_id]:
                errors.append(
                    {
                        "type": "OUTGOING_NOT_ON_COURT",
                        "period": period,
                        "team_id": team_id,
                        "outgoing_id": outgoing,
                        "description": r["_description"],
                    }
                )
                continue
            if incoming is None:
                errors.append(
                    {
                        "type": "INCOMING_UNRESOLVED",
                        "period": period,
                        "team_id": team_id,
                        "description": r["_description"],
                    }
                )
                continue
            if incoming in lineups[team_id]:
                errors.append(
                    {
                        "type": "INCOMING_ALREADY_ON_COURT",
                        "period": period,
                        "team_id": team_id,
                        "incoming_id": incoming,
                        "description": r["_description"],
                    }
                )
                continue

            lineups[team_id].remove(outgoing)
            lineups[team_id].add(incoming)
            if len(lineups[team_id]) != 5:
                errors.append(
                    {
                        "type": "IMPOSSIBLE_LINEUP_SIZE",
                        "period": period,
                        "team_id": team_id,
                        "size": len(lineups[team_id]),
                    }
                )

        for team_id in teams:
            if len(lineups[int(team_id)]) == 5:
                delta = max(0.0, period_end - last_time[int(team_id)])
                for pid in lineups[int(team_id)]:
                    seconds[pid] += delta

    comparison = roster.copy()
    comparison["reconstructed_minutes"] = comparison["player_id"].map(
        lambda x: seconds.get(int(x), 0.0) / 60.0
    )
    comparison["minute_error"] = (
        comparison["reconstructed_minutes"] - comparison["official_minutes"]
    )
    comparison["abs_minute_error"] = comparison["minute_error"].abs()

    metrics = {
        "max_period": max_period,
        "game_minutes": game_seconds / 60.0,
        "expected_team_player_minutes": game_seconds * 5 / 60.0,
        "mae_minutes_all_roster": float(comparison["abs_minute_error"].mean()),
        "max_abs_error_minutes": float(comparison["abs_minute_error"].max()),
        "players_error_gt_0_25": int((comparison["abs_minute_error"] > 0.25).sum()),
        "players_error_gt_1_0": int((comparison["abs_minute_error"] > 1.0).sum()),
        "errors_count": len(errors),
        "error_types": dict(pd.Series([x["type"] for x in errors]).value_counts())
        if errors
        else {},
        "substitution_resolution_count": len(resolutions),
        "unresolved_substitutions": int(
            sum(x["incoming_id"] is None for x in resolutions)
        ),
        "period_starter_info": period_starter_info,
        "errors": errors[:100],
    }

    team_totals = []
    for team_id, g in comparison.groupby("team_id"):
        team_totals.append(
            {
                "team_id": int(team_id),
                "official_total_minutes": float(g["official_minutes"].sum()),
                "reconstructed_total_minutes": float(g["reconstructed_minutes"].sum()),
                "expected_total_minutes": float(game_seconds * 5 / 60.0),
            }
        )
    metrics["team_totals"] = team_totals

    # Strict feasibility gate. Failure is evidence, not a crash.
    metrics["truth_test_pass"] = bool(
        metrics["unresolved_substitutions"] == 0
        and metrics["errors_count"] == 0
        and metrics["max_abs_error_minutes"] <= 0.25
        and all(
            abs(x["reconstructed_total_minutes"] - x["expected_total_minutes"]) <= 0.25
            for x in team_totals
        )
    )
    return comparison, metrics


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="research/p0_s2/poc04/results")
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--sleep-seconds", type=float, default=1.5)
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    report = {
        "poc": "P0-S2 POC-04",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "results": [],
    }

    for season in SEASONS:
        item = {"season": season}
        try:
            gid = discover_game(season, args.timeout)
            item["game_id"] = gid
            time.sleep(args.sleep_seconds)

            pbp = fetch_pbp(gid, args.timeout)
            time.sleep(args.sleep_seconds)
            box = fetch_box(gid, args.timeout)

            roster, lookup = build_roster(box)
            comparison, metrics = reconstruct(pbp, roster, lookup)

            comparison.sort_values(
                ["team_id", "official_minutes"], ascending=[True, False]
            ).to_csv(out / f"{season}_{gid}_minute_comparison.csv", index=False)

            item.update(metrics)
            item["status"] = "PASS" if metrics["truth_test_pass"] else "FAIL"
        except Exception as exc:
            item.update(
                {
                    "status": "ERROR",
                    "exception_type": type(exc).__name__,
                    "exception": str(exc),
                }
            )

        report["results"].append(item)
        time.sleep(args.sleep_seconds)

    (out / "poc04_report.json").write_text(
        json.dumps(report, indent=2, default=json_default), encoding="utf-8"
    )

    lines = [
        "P0-S2 POC-04 — Rotation Reconstruction Truth Test",
        f"Run UTC: {report['run_utc']}",
        "",
    ]
    for r in report["results"]:
        lines.extend(
            [
                f"Season {r['season']} | GAME_ID={r.get('game_id', 'n/a')}",
                f"  STATUS: {r.get('status')}",
                f"  game_minutes={r.get('game_minutes', 'n/a')}",
                f"  expected team-player minutes={r.get('expected_team_player_minutes', 'n/a')}",
                f"  MAE minutes={r.get('mae_minutes_all_roster', 'n/a')}",
                f"  max abs error minutes={r.get('max_abs_error_minutes', 'n/a')}",
                f"  players >0.25 min error={r.get('players_error_gt_0_25', 'n/a')}",
                f"  players >1.0 min error={r.get('players_error_gt_1_0', 'n/a')}",
                f"  substitutions resolved={r.get('substitution_resolution_count', 'n/a')}",
                f"  unresolved substitutions={r.get('unresolved_substitutions', 'n/a')}",
                f"  reconstruction errors={r.get('errors_count', 'n/a')}",
                f"  error types={r.get('error_types', 'n/a')}",
            ]
        )
        if r.get("team_totals"):
            for x in r["team_totals"]:
                lines.append(
                    "  TEAM "
                    f"{x['team_id']}: official={x['official_total_minutes']:.3f} "
                    f"reconstructed={x['reconstructed_total_minutes']:.3f} "
                    f"expected={x['expected_total_minutes']:.3f}"
                )
        if r.get("exception"):
            lines.append(f"  ERROR: {r['exception']}")
        lines.append("")

    statuses = [x.get("status") for x in report["results"]]
    overall = "PASS" if statuses and all(x == "PASS" for x in statuses) else "FAIL/INVESTIGATE"
    lines.append(f"OVERALL: {overall}")
    lines.append(
        "A failure is useful evidence. Do not loosen the thresholds or guess missing lineups just to force PASS."
    )
    text = "\n".join(lines)
    (out / "poc04_summary.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
