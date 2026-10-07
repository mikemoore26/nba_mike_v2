from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"

REQUIRED = [
    "docs/CANONICAL_DATA_CONTRACT.md",
    "docs/P0_S3_CANONICAL_DATA_ARCHITECTURE.md",
    "docs/P0_S3_MILESTONE_PLAN.md",
    "docs/STORAGE_MANIFEST_STANDARD.md",
    "docs/CANONICAL_IDENTITY_STANDARD.md",
    "docs/SCHEMA_VALIDATION_STANDARD.md",
    "docs/CANONICAL_BUILD_STANDARD.md",
    "docs/POINT_IN_TIME_SNAPSHOT_STANDARD.md",
    "docs/PACKAGING_EXECUTION_STANDARD.md",
    "docs/LEAKAGE_INVARIANT_STANDARD.md",
    "docs/HISTORICAL_RECONSTRUCTION_STANDARD.md",
    "docs/P0_S3_CLOSEOUT.md",
    "research/p0_s3/s8/results/s8_historical_reconstruction_report.json",
    "research/p0_s3/s8/results/s8_acceptance_report.json",
]

UNRESOLVED_TERMS = (
    "injuries",
    "confirmed starting lineups",
    "news",
    "sportsbook props",
    "rotation/stint",
)

def main() -> int:
    checks = {}
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    checks["required_artifacts"] = not missing

    closeout_path = ROOT / "docs/P0_S3_CLOSEOUT.md"
    closeout = closeout_path.read_text(encoding="utf-8") if closeout_path.exists() else ""
    checks["scoped_pass_language"] = (
        "PASS — scoped to the canonical historical statistical-data foundation." in closeout
        and "No profitability claim is made." in closeout
    )
    checks["unresolved_domains_preserved"] = all(term in closeout for term in UNRESOLVED_TERMS)
    checks["d1_boundary_preserved"] = "D-1" in closeout and "Same-day earlier-game information is intentionally excluded" in closeout

    s8_path = ROOT / "research/p0_s3/s8/results/s8_historical_reconstruction_report.json"
    if s8_path.exists():
        s8 = json.loads(s8_path.read_text(encoding="utf-8"))
        seasons = s8.get("seasons", [])
        checks["s8_three_season_evidence"] = (
            s8.get("overall_pass") is True
            and [x.get("season") for x in seasons] == ["2019-20", "2023-24", "2025-26"]
            and all(x.get("pass") is True for x in seasons)
        )
        checks["intraday_not_overclaimed"] = s8.get("intraday_domains_solved") is False
    else:
        checks["s8_three_season_evidence"] = False
        checks["intraday_not_overclaimed"] = False

    proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT)
    checks["full_regression_suite"] = proc.returncode == 0

    overall = all(checks.values())
    report = {
        "milestone": "P0-S3 S9",
        "decision": "PASS" if overall else "FAIL",
        "scope": "canonical historical statistical-data foundation",
        "checks": checks,
        "missing_artifacts": missing,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "s9_closeout_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (RESULTS / "s9_closeout_summary.txt").write_text(
        "\n".join([
            "P0-S3 S9 — Closeout",
            *[f"{k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items()],
            f"DECISION: {'PASS' if overall else 'FAIL'}",
            "SCOPE: canonical historical statistical-data foundation",
        ]) + "\n",
        encoding="utf-8",
    )

    print("P0-S3 S9 — Closeout")
    for key, value in checks.items():
        print(f"  {key}: {'PASS' if value else 'FAIL'}")
    if missing:
        print("  missing:")
        for item in missing:
            print(f"    - {item}")
    print(f"DECISION: {'PASS' if overall else 'FAIL'}")
    print("SCOPE: canonical historical statistical-data foundation")
    return 0 if overall else 1

if __name__ == "__main__":
    raise SystemExit(main())
