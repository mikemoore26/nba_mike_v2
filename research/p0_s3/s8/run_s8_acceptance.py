"""Acceptance wrapper for P0-S3 S8."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULT = HERE / "results" / "s8_historical_reconstruction_report.json"


def main() -> int:
    checks = {}

    proc = subprocess.run(
        [sys.executable, str(HERE / "run_s8_historical_reconstruction.py")],
        cwd=Path.cwd(),
        text=True,
    )
    checks["historical_runner"] = proc.returncode == 0 and RESULT.exists()

    if RESULT.exists():
        report = json.loads(RESULT.read_text(encoding="utf-8"))
        seasons = report.get("seasons", [])
        checks["three_season_anchors"] = [x.get("season") for x in seasons] == [
            "2019-20", "2023-24", "2025-26"
        ]
        checks["all_seasons_pass"] = len(seasons) == 3 and all(x.get("pass") is True for x in seasons)
        checks["d1_cutoff"] = len(seasons) == 3 and all(x.get("d1_cutoff_pass") is True for x in seasons)
        checks["target_delta"] = len(seasons) == 3 and all(x.get("target_delta_pass") is True for x in seasons)
        checks["deterministic_rebuild"] = len(seasons) == 3 and all(
            x.get("deterministic_rebuild_pass") is True for x in seasons
        )
        checks["intraday_not_overclaimed"] = report.get("intraday_domains_solved") is False
    else:
        for key in (
            "three_season_anchors", "all_seasons_pass", "d1_cutoff", "target_delta",
            "deterministic_rebuild", "intraday_not_overclaimed"
        ):
            checks[key] = False

    tests = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=Path.cwd())
    checks["full_regression_suite"] = tests.returncode == 0

    overall = all(checks.values())
    print("P0-S3 S8 — Historical Reconstruction Acceptance")
    for name, passed in checks.items():
        print(f"  {name}: {'PASS' if passed else 'FAIL'}")
    print(f"OVERALL: {'PASS' if overall else 'FAIL'}")

    out = {"milestone": "P0-S3 S8", "checks": checks, "overall_pass": overall}
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "s8_acceptance_report.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
