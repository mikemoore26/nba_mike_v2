"""P0-S3 S8: real historical reconstruction sample.

Requires nba_api, which was already used during P0-S2 feasibility work.
This runner does not train a model and does not claim intraday truth.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

from nba_mike.reconstruction import (
    canonicalize_player_game_rows,
    choose_representative_target_date,
    reconstruct_d1_rows,
    summarize_target_date_delta,
)

SEASONS = ("2019-20", "2023-24", "2025-26")
ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def stable_hash(rows):
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fetch_player_game_logs(season: str):
    try:
        from nba_api.stats.endpoints import playergamelogs
    except ImportError as exc:
        raise RuntimeError(
            "nba_api is required for the real S8 sample. Install/use the same dependency "
            "that supported P0-S2 NBA Stats feasibility work."
        ) from exc

    response = playergamelogs.PlayerGameLogs(
        season_nullable=season,
        season_type_nullable="Regular Season",
        timeout=90,
    )
    frames = response.get_data_frames()
    if not frames or frames[0].empty:
        raise RuntimeError(f"No PlayerGameLogs rows returned for {season}.")
    return frames[0].to_dict(orient="records")


def audit_season(season: str) -> dict:
    source_rows = fetch_player_game_logs(season)
    canonical = canonicalize_player_game_rows(source_rows)
    target_date = choose_representative_target_date(source_rows, fraction=0.35)
    d1_a = reconstruct_d1_rows(source_rows, target_date)
    d1_b = reconstruct_d1_rows(list(reversed(source_rows)), target_date)
    delta = summarize_target_date_delta(source_rows, target_date)

    target_rows = [r for r in canonical if r["event_date"] == target_date]
    result = {
        "season": season,
        "source_row_count": len(source_rows),
        "canonical_row_count": len(canonical),
        "target_date": target_date,
        "target_date_player_rows": len(target_rows),
        "d1_row_count": len(d1_a),
        "d1_max_event_date": max((r["event_date"] for r in d1_a), default=None),
        "d1_cutoff_pass": all(r["event_date"] < target_date for r in d1_a),
        "target_delta_pass": delta["pass"],
        "wrong_target_player_delta_count": len(delta["wrong_target_player_deltas"]),
        "wrong_non_target_player_delta_count": len(delta["wrong_non_target_player_deltas"]),
        "deterministic_rebuild_pass": stable_hash(d1_a) == stable_hash(d1_b),
        "snapshot_hash": stable_hash(d1_a),
    }
    result["pass"] = all(
        (
            result["source_row_count"] > 0,
            result["target_date_player_rows"] > 0,
            result["d1_cutoff_pass"],
            result["target_delta_pass"],
            result["deterministic_rebuild_pass"],
        )
    )
    return result


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    report = {
        "milestone": "P0-S3 S8",
        "scope": "Historical Reconstruction Sample",
        "governing_rule": "For target game date D, statistical evidence is eligible only through D-1.",
        "intraday_domains_solved": False,
        "seasons": [],
    }

    print("P0-S3 S8 — Historical Reconstruction Sample")
    for idx, season in enumerate(SEASONS):
        try:
            result = audit_season(season)
        except Exception as exc:
            result = {"season": season, "pass": False, "error": f"{type(exc).__name__}: {exc}"}
        report["seasons"].append(result)
        status = "PASS" if result.get("pass") else "FAIL"
        print(f"  {season}: {status}")
        if result.get("target_date"):
            print(
                f"    target={result['target_date']} source_rows={result['source_row_count']} "
                f"d1_rows={result['d1_row_count']} target_rows={result['target_date_player_rows']}"
            )
        if result.get("error"):
            print(f"    error={result['error']}")
        if idx < len(SEASONS) - 1:
            time.sleep(0.7)

    report["overall_pass"] = all(x.get("pass") is True for x in report["seasons"])
    (RESULTS / "s8_historical_reconstruction_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    lines = [
        "P0-S3 S8 — Historical Reconstruction Sample",
        *[
            f"{x['season']}: {'PASS' if x.get('pass') else 'FAIL'}"
            + (f" | target={x.get('target_date')} | D-1 rows={x.get('d1_row_count')}" if x.get("target_date") else "")
            for x in report["seasons"]
        ],
        f"OVERALL: {'PASS' if report['overall_pass'] else 'FAIL'}",
        "NOTE: This does not solve intraday injuries, confirmed lineups, news, odds, line movement, or ambiguous rotation truth.",
    ]
    (RESULTS / "s8_historical_reconstruction_summary.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(f"OVERALL: {'PASS' if report['overall_pass'] else 'FAIL'}")
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
