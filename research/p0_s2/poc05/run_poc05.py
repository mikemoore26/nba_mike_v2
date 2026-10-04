"""P0-S2 POC-05 — Starter & Period-Start Lineup Feasibility.

Research-only. This experiment does NOT build production lineup data.

Questions:
1. Does the official traditional box score expose authoritative game starters?
2. Can those starters seed Q1?
3. Can later-period starting lineups be solved from substitution constraints
   without guessing from player activity?
4. When a period lineup is solved, does forward reconstruction reproduce
   official player minutes?

The solver uses substitution state constraints:
- OUT player must be ON immediately before a substitution.
- IN player must be OFF immediately before a substitution.
- after substitution, OUT is OFF and IN is ON.

For each team/period it searches combinations of five players from the official
game roster and keeps only starting lineups that satisfy the full substitution
sequence. A unique solution is evidence; multiple solutions remain ambiguous.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import re
import time
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from nba_api.stats.endpoints import (
    boxscoretraditionalv3,
    leaguegamelog,
    playbyplayv3,
)

SEASONS = ("2025-26", "2023-24", "2019-20")


def json_default(value):
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
    raise TypeError(f"Not JSON serializable: {type(value).__name__}")


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
    frames = playbyplayv3.PlayByPlayV3(game_id=game_id, timeout=timeout).get_data_frames()
    if not frames:
        raise RuntimeError("No PBP frames")
    return frames[0].copy()


def fetch_box(game_id: str, timeout: int) -> pd.DataFrame:
    frames = boxscoretraditionalv3.BoxScoreTraditionalV3(
        game_id=game_id, timeout=timeout
    ).get_data_frames()
    for df in frames:
        cols = set(df.columns)
        if ("personId" in cols or "PLAYER_ID" in cols) and (
            "minutes" in cols or "MIN" in cols
        ):
            return df.copy()
    raise RuntimeError(f"No player box frame. Schemas={[list(x.columns) for x in frames]}")


def col(df: pd.DataFrame, *names: str) -> str:
    for x in names:
        if x in df.columns:
            return x
    raise KeyError(names)


def normalize_name(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("’", "'")
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    toks = [t for t in text.split() if t not in {"jr", "sr", "ii", "iii", "iv"}]
    return " ".join(toks)


def parse_minutes(value: object) -> float:
    if value is None or pd.isna(value):
        return 0.0
    text = str(value).strip()
    if not text:
        return 0.0
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


def clock_seconds(value: object) -> float:
    text = str(value)
    m = re.fullmatch(r"PT(?:(\d+)M)?([0-9.]+)S", text)
    if m:
        return int(m.group(1) or 0) * 60 + float(m.group(2))
    m = re.fullmatch(r"(\d+):([0-9.]+)", text)
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    raise ValueError(text)


def period_len(period: int) -> float:
    return 720.0 if period <= 4 else 300.0


def period_elapsed(clock: object, period: int) -> float:
    return period_len(period) - clock_seconds(clock)


def parse_incoming(description: object) -> str | None:
    m = re.match(r"SUB:\s*(.+?)\s+FOR\s+(.+?)\s*$", str(description), flags=re.I)
    return m.group(1).strip() if m else None


def build_roster(box: pd.DataFrame):
    pidc = col(box, "personId", "PLAYER_ID")
    teamc = col(box, "teamId", "TEAM_ID")
    minc = col(box, "minutes", "MIN")

    namec = next((x for x in ("name", "playerName", "PLAYER_NAME") if x in box.columns), None)
    firstc = next((x for x in ("firstName",) if x in box.columns), None)
    familyc = next((x for x in ("familyName",) if x in box.columns), None)
    starterc = next(
        (x for x in ("position", "POSITION", "starter", "isStarter") if x in box.columns),
        None,
    )

    rows = []
    for _, r in box.iterrows():
        if pd.isna(r[pidc]) or pd.isna(r[teamc]):
            continue
        if namec:
            name = str(r[namec])
        elif firstc and familyc:
            name = f"{r[firstc]} {r[familyc]}"
        else:
            name = str(r[pidc])

        starter_raw = r[starterc] if starterc else None
        if starterc in ("position", "POSITION"):
            is_starter = bool(str(starter_raw).strip())
        elif starterc:
            is_starter = str(starter_raw).lower() in {"true", "1", "yes"}
        else:
            is_starter = False

        rows.append({
            "player_id": int(r[pidc]),
            "team_id": int(r[teamc]),
            "player_name": name,
            "normalized_name": normalize_name(name),
            "official_minutes": parse_minutes(r[minc]),
            "starter_field": starterc,
            "starter_raw": None if starter_raw is None or pd.isna(starter_raw) else str(starter_raw),
            "is_game_starter": is_starter,
        })

    roster = pd.DataFrame(rows)
    lookup = defaultdict(lambda: defaultdict(list))
    for rec in roster.to_dict("records"):
        team = rec["team_id"]
        full = rec["normalized_name"]
        lookup[team][full].append(rec)
        if full:
            lookup[team][full.split()[-1]].append(rec)
    return roster, lookup


def resolve_name(text: str, team_id: int, lookup) -> int | None:
    norm = normalize_name(text)
    for key in (norm, norm.split()[-1] if norm else ""):
        candidates = lookup.get(team_id, {}).get(key, [])
        unique = {x["player_id"] for x in candidates}
        if len(unique) == 1:
            return next(iter(unique))
    return None


def prepare_subs(pbp: pd.DataFrame, lookup):
    teamc = col(pbp, "teamId", "TEAM_ID")
    personc = col(pbp, "personId", "PERSON_ID")
    periodc = col(pbp, "period", "PERIOD")
    clockc = col(pbp, "clock", "CLOCK")
    actionc = col(pbp, "actionType", "ACTION_TYPE")
    desc = col(pbp, "description", "DESCRIPTION")
    aid = col(pbp, "actionId", "ACTION_ID")

    subs = pbp[pbp[actionc].astype(str).str.lower().eq("substitution")].copy()
    out = []
    for _, r in subs.iterrows():
        if pd.isna(r[teamc]) or pd.isna(r[personc]):
            continue
        team = int(r[teamc])
        incoming_text = parse_incoming(r[desc])
        incoming = resolve_name(incoming_text, team, lookup) if incoming_text else None
        out.append({
            "team_id": team,
            "period": int(r[periodc]),
            "clock": str(r[clockc]),
            "period_elapsed": period_elapsed(r[clockc], int(r[periodc])),
            "action_id": int(r[aid]),
            "out_id": int(r[personc]),
            "in_id": incoming,
            "incoming_text": incoming_text,
            "description": str(r[desc]),
        })
    return pd.DataFrame(out)


def valid_start_lineups(players: list[int], subs: pd.DataFrame) -> list[tuple[int, ...]]:
    """Return all 5-player starts consistent with the substitution sequence."""
    if len(players) < 5:
        return []

    ordered = subs.sort_values(["period_elapsed", "action_id"], kind="stable")
    valid = []
    for combo in itertools.combinations(players, 5):
        on = set(combo)
        ok = True
        for _, r in ordered.iterrows():
            out_id = int(r["out_id"])
            if pd.isna(r["in_id"]):
                ok = False
                break
            in_id = int(r["in_id"])
            if out_id not in on or in_id in on:
                ok = False
                break
            on.remove(out_id)
            on.add(in_id)
            if len(on) != 5:
                ok = False
                break
        if ok:
            valid.append(tuple(sorted(combo)))
    return valid


def reconstruct_period(start: tuple[int, ...], subs: pd.DataFrame, period: int):
    on = set(start)
    last = 0.0
    seconds = defaultdict(float)
    errors = []

    ordered = subs.sort_values(["period_elapsed", "action_id"], kind="stable")
    for _, r in ordered.iterrows():
        t = float(r["period_elapsed"])
        delta = max(0.0, t - last)
        for pid in on:
            seconds[pid] += delta
        last = t

        out_id = int(r["out_id"])
        if pd.isna(r["in_id"]):
            errors.append("UNRESOLVED_INCOMING")
            continue
        in_id = int(r["in_id"])
        if out_id not in on:
            errors.append("OUT_NOT_ON")
            continue
        if in_id in on:
            errors.append("IN_ALREADY_ON")
            continue
        on.remove(out_id)
        on.add(in_id)

    delta = max(0.0, period_len(period) - last)
    for pid in on:
        seconds[pid] += delta
    return seconds, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="research/p0_s2/poc05/results")
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--sleep-seconds", type=float, default=1.5)
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    report = {
        "poc": "P0-S2 POC-05",
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
            subs = prepare_subs(pbp, lookup)

            item["box_columns"] = list(box.columns)
            item["starter_field"] = (
                roster["starter_field"].dropna().iloc[0]
                if roster["starter_field"].notna().any()
                else None
            )
            game_starters = roster[roster["is_game_starter"]]
            item["game_starter_count_by_team"] = {
                str(int(k)): int(v)
                for k, v in game_starters.groupby("team_id").size().to_dict().items()
            }

            max_period = int(pd.to_numeric(pbp[col(pbp, "period", "PERIOD")]).max())
            total_seconds = defaultdict(float)
            period_results = []

            for team_id in sorted(roster["team_id"].unique()):
                active_players = roster[
                    (roster["team_id"] == team_id) & (roster["official_minutes"] > 0)
                ]["player_id"].astype(int).tolist()

                for period in range(1, max_period + 1):
                    s = subs[(subs["team_id"] == team_id) & (subs["period"] == period)].copy()
                    solutions = valid_start_lineups(active_players, s)

                    authoritative_q1 = tuple(sorted(
                        roster[
                            (roster["team_id"] == team_id)
                            & roster["is_game_starter"]
                        ]["player_id"].astype(int).tolist()
                    ))

                    q1_match = None
                    if period == 1 and len(authoritative_q1) == 5:
                        q1_match = authoritative_q1 in solutions

                    pr = {
                        "team_id": int(team_id),
                        "period": period,
                        "substitutions": int(len(s)),
                        "candidate_active_players": len(active_players),
                        "constraint_solution_count": len(solutions),
                        "unique_solution": len(solutions) == 1,
                        "q1_authoritative_starters_available": period == 1 and len(authoritative_q1) == 5,
                        "q1_authoritative_starters_satisfy_constraints": q1_match,
                        "solution_examples": [list(x) for x in solutions[:10]],
                    }

                    if len(solutions) == 1:
                        secs, errs = reconstruct_period(solutions[0], s, period)
                        pr["reconstruction_errors"] = errs
                        for pid, val in secs.items():
                            total_seconds[pid] += val
                    else:
                        pr["reconstruction_errors"] = ["AMBIGUOUS_PERIOD_START"]

                    period_results.append(pr)

            comp = roster.copy()
            comp["constraint_reconstructed_minutes"] = comp["player_id"].map(
                lambda x: total_seconds.get(int(x), 0.0) / 60.0
            )
            comp["minute_error"] = (
                comp["constraint_reconstructed_minutes"] - comp["official_minutes"]
            )
            comp["abs_minute_error"] = comp["minute_error"].abs()
            comp.to_csv(out / f"{season}_{gid}_constraint_minute_comparison.csv", index=False)

            pd.DataFrame(period_results).to_csv(
                out / f"{season}_{gid}_period_solution_counts.csv", index=False
            )

            item["period_results"] = period_results
            item["unique_periods"] = int(sum(x["unique_solution"] for x in period_results))
            item["total_team_periods"] = len(period_results)
            item["ambiguous_periods"] = len(period_results) - item["unique_periods"]
            item["q1_authoritative_checks"] = [
                x for x in period_results if x["period"] == 1
            ]
            item["mae_minutes_if_unique_periods_only"] = float(comp["abs_minute_error"].mean())
            item["max_abs_error_if_unique_periods_only"] = float(comp["abs_minute_error"].max())

            # This POC is feasibility-oriented. PASS requires authoritative Q1
            # starters for both teams and at least one later period uniquely
            # solved by constraints. Full all-period uniqueness is NOT assumed.
            q1_ok = (
                len(item["q1_authoritative_checks"]) == 2
                and all(
                    x["q1_authoritative_starters_available"]
                    and x["q1_authoritative_starters_satisfy_constraints"] is True
                    for x in item["q1_authoritative_checks"]
                )
            )
            later_unique = any(
                x["period"] > 1 and x["unique_solution"] for x in period_results
            )
            item["status"] = "PASS" if q1_ok and later_unique else "INVESTIGATE"

        except Exception as exc:
            item.update({
                "status": "ERROR",
                "exception_type": type(exc).__name__,
                "exception": str(exc),
            })

        report["results"].append(item)
        time.sleep(args.sleep_seconds)

    (out / "poc05_report.json").write_text(
        json.dumps(report, indent=2, default=json_default), encoding="utf-8"
    )

    lines = [
        "P0-S2 POC-05 — Starter & Period-Start Lineup Feasibility",
        f"Run UTC: {report['run_utc']}",
        "",
    ]
    for r in report["results"]:
        lines += [
            f"Season {r['season']} | GAME_ID={r.get('game_id','n/a')}",
            f"  STATUS: {r.get('status')}",
            f"  starter field={r.get('starter_field')}",
            f"  game starters by team={r.get('game_starter_count_by_team')}",
            f"  unique team-period starts={r.get('unique_periods','n/a')}/{r.get('total_team_periods','n/a')}",
            f"  ambiguous team-period starts={r.get('ambiguous_periods','n/a')}",
        ]
        for x in r.get("q1_authoritative_checks", []):
            lines.append(
                f"  Q1 TEAM {x['team_id']}: official starters available="
                f"{x['q1_authoritative_starters_available']} | "
                f"satisfy substitution constraints="
                f"{x['q1_authoritative_starters_satisfy_constraints']} | "
                f"constraint solutions={x['constraint_solution_count']}"
            )
        if r.get("exception"):
            lines.append(f"  ERROR: {r['exception']}")
        lines.append("")

    lines.append("INTERPRETATION RULE:")
    lines.append(
        "A unique constraint solution is evidence. Multiple valid solutions remain ambiguous and must not be guessed."
    )
    text = "\n".join(lines)
    (out / "poc05_summary.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
