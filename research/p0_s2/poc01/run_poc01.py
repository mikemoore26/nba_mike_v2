"""P0-S2 POC-01: Core NBA historical data and identity probe.

Research-only. This does not create production datasets or models.
It tests whether nba_api / stats.nba.com can practically return representative
historical team/player game logs with stable identifiers and expected schemas.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import leaguegamelog, playergamelogs

SEASONS = ("2025-26", "2023-24", "2019-20")
REQUIRED_TEAM = {
    "SEASON_ID", "TEAM_ID", "TEAM_ABBREVIATION", "GAME_ID", "GAME_DATE",
    "MATCHUP", "MIN", "FGA", "FG3A", "FTA", "REB", "AST", "PTS",
}
REQUIRED_PLAYER = {
    "SEASON_YEAR", "PLAYER_ID", "PLAYER_NAME", "TEAM_ID",
    "TEAM_ABBREVIATION", "GAME_ID", "GAME_DATE", "MATCHUP", "MIN",
    "FGA", "FG3A", "FTA", "REB", "AST", "PTS",
}


def fetch_team(season: str, timeout: int) -> pd.DataFrame:
    return leaguegamelog.LeagueGameLog(
        season=season,
        season_type_all_star="Regular Season",
        player_or_team_abbreviation="T",
        timeout=timeout,
    ).get_data_frames()[0]


def fetch_player(season: str, timeout: int) -> pd.DataFrame:
    return playergamelogs.PlayerGameLogs(
        season_nullable=season,
        season_type_nullable="Regular Season",
        timeout=timeout,
    ).get_data_frames()[0]


def audit_frame(df: pd.DataFrame, required: set[str], kind: str) -> dict:
    missing_columns = sorted(required - set(df.columns))
    result = {
        "kind": kind,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "missing_required_columns": missing_columns,
        "duplicate_full_rows": int(df.duplicated().sum()) if len(df) else 0,
    }

    for col in ("GAME_ID", "TEAM_ID", "PLAYER_ID", "GAME_DATE", "MIN", "PTS"):
        if col in df.columns:
            result[f"null_rate_{col}"] = float(df[col].isna().mean()) if len(df) else None

    if kind == "team" and len(df) and "GAME_ID" in df.columns:
        counts = df.groupby("GAME_ID").size()
        result["unique_games"] = int(df["GAME_ID"].nunique())
        result["games_not_exactly_two_team_rows"] = int((counts != 2).sum())

    if kind == "player" and len(df):
        result["unique_players"] = int(df["PLAYER_ID"].nunique()) if "PLAYER_ID" in df else 0
        result["unique_games"] = int(df["GAME_ID"].nunique()) if "GAME_ID" in df else 0
        if {"PLAYER_ID", "GAME_ID"}.issubset(df.columns):
            result["duplicate_player_game_keys"] = int(
                df.duplicated(subset=["PLAYER_ID", "GAME_ID"]).sum()
            )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="research/p0_s2/poc01/results")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--sleep-seconds", type=float, default=1.5)
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    report = {
        "poc": "P0-S2 POC-01",
        "purpose": "core historical data and identity feasibility",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "seasons": list(SEASONS),
        "results": [],
    }

    failures = 0

    for season in SEASONS:
        season_result = {"season": season}

        for kind, fetcher, required in (
            ("team", fetch_team, REQUIRED_TEAM),
            ("player", fetch_player, REQUIRED_PLAYER),
        ):
            started = time.perf_counter()
            try:
                df = fetcher(season, args.timeout)
                elapsed = time.perf_counter() - started
                audit = audit_frame(df, required, kind)
                audit["request_seconds"] = round(elapsed, 3)
                audit["status"] = "PASS" if len(df) and not audit["missing_required_columns"] else "FAIL"

                sample_cols = [
                    c for c in (
                        "SEASON_ID", "SEASON_YEAR", "GAME_ID", "GAME_DATE",
                        "TEAM_ID", "TEAM_ABBREVIATION", "PLAYER_ID",
                        "PLAYER_NAME", "MATCHUP", "MIN", "FGA", "FG3A",
                        "FTA", "REB", "AST", "PTS"
                    ) if c in df.columns
                ]
                df[sample_cols].head(25).to_csv(
                    out / f"{season}_{kind}_sample.csv", index=False
                )

                schema = {
                    "columns": list(df.columns),
                    "dtypes": {c: str(t) for c, t in df.dtypes.items()},
                }
                (out / f"{season}_{kind}_schema.json").write_text(
                    json.dumps(schema, indent=2), encoding="utf-8"
                )

                if audit["status"] != "PASS":
                    failures += 1
            except Exception as exc:
                elapsed = time.perf_counter() - started
                audit = {
                    "kind": kind,
                    "status": "ERROR",
                    "request_seconds": round(elapsed, 3),
                    "exception_type": type(exc).__name__,
                    "exception": str(exc),
                }
                failures += 1

            season_result[kind] = audit
            time.sleep(args.sleep_seconds)

        report["results"].append(season_result)

    (out / "poc01_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    lines = [
        "P0-S2 POC-01 — Core NBA Historical Data & Identity Test",
        f"Run UTC: {report['run_utc']}",
        "",
    ]
    for item in report["results"]:
        lines.append(f"Season {item['season']}")
        for kind in ("team", "player"):
            r = item[kind]
            lines.append(
                f"  {kind.upper()}: {r.get('status')} | "
                f"rows={r.get('rows', 'n/a')} | "
                f"seconds={r.get('request_seconds', 'n/a')}"
            )
            if r.get("exception"):
                lines.append(f"    error={r['exception']}")
            if r.get("missing_required_columns"):
                lines.append(f"    missing={r['missing_required_columns']}")
        lines.append("")

    overall = "PASS" if failures == 0 else "PARTIAL/FAIL"
    lines.append(f"OVERALL: {overall}")
    lines.append("NOTE: Endpoint access failure is a valid feasibility finding; do not work around it silently.")
    text = "\n".join(lines)
    (out / "poc01_summary.txt").write_text(text, encoding="utf-8")
    print(text)

    # Research POC returns zero so results are preserved even if a source fails.
    # The report itself records PASS/ERROR; source failure is evidence, not a script crash.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
