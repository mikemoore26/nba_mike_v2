from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from nba_mike.snapshots.builder import SnapshotError, build_d1_snapshot
from nba_mike.validation.invariants import (
    InvariantError, assert_d1_boundary, assert_entity_history_contract,
    assert_feature_target_separation, assert_snapshot_metadata,
    assert_team_opponent_consistency, assert_unique_keys,
)

ROOT = Path(__file__).resolve().parents[3]
RESULTS = Path(__file__).resolve().parent / "results"


def catches(fn, token: str) -> bool:
    try:
        fn()
    except Exception as exc:
        return token in str(exc)
    return False


def main() -> int:
    checks: dict[str, bool] = {}
    checks["d1_target_day_blocked"] = catches(
        lambda: assert_d1_boundary([{"event_date":"2026-10-03"}], target_game_date="2026-10-03"),
        "D1_LEAKAGE",
    )
    checks["future_day_blocked"] = catches(
        lambda: assert_d1_boundary([{"event_date":"2026-10-04"}], target_game_date="2026-10-03"),
        "D1_LEAKAGE",
    )
    checks["duplicate_key_blocked"] = catches(
        lambda: assert_unique_keys([{"game_id":"g","player_id":"p"},{"game_id":"g","player_id":"p"}]),
        "DUPLICATE_KEY",
    )
    checks["team_opponent_consistency"] = catches(
        lambda: assert_team_opponent_consistency([{"team_id":"t","opponent_team_id":"t"}]),
        "TEAM_EQUALS_OPPONENT",
    )
    checks["target_separation"] = catches(
        lambda: assert_feature_target_separation([{"actual_points":20}], forbidden_target_fields={"actual_points"}),
        "TARGET_LEAKAGE",
    )
    checks["zero_history_contract"] = catches(
        lambda: assert_entity_history_contract({"entity_history":[{"eligible_game_count":0,"history_status":"AVAILABLE"}]}),
        "ENTITY_HISTORY_STATUS_INVALID",
    )

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "parent.json"
        p.write_text('{"canonical":true}', encoding="utf-8")
        manifest = {"artifact_id":"parent-1", "sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                    "relative_path":"canonical/parent.json", "validation_status":"PASS"}
        rows = [
            {"game_id":"g1","event_date":"2026-10-01","player_id":"p1","team_id":"t1"},
            {"game_id":"g2","event_date":"2026-10-03","player_id":"p1","team_id":"t1"},
        ]
        eligible, meta = build_d1_snapshot(rows, target_game_date="2026-10-03",
                                           parent_manifest=manifest, parent_artifact_path=p,
                                           expected_entities=[{"player_id":"rookie","team_id":"t2"}])
        try:
            assert_d1_boundary(eligible, target_game_date="2026-10-03")
            assert_unique_keys(eligible)
            assert_snapshot_metadata(meta, target_game_date="2026-10-03")
            assert_entity_history_contract(meta)
            checks["governed_snapshot_passes"] = True
        except InvariantError:
            checks["governed_snapshot_passes"] = False
        tampered = dict(manifest); tampered["validation_status"] = "QUARANTINED"
        checks["non_pass_parent_blocked"] = catches(
            lambda: build_d1_snapshot(rows, target_game_date="2026-10-03", parent_manifest=tampered, parent_artifact_path=p),
            "validation_status must be PASS",
        )

    proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, capture_output=True, text=True)
    checks["full_regression_suite"] = proc.returncode == 0
    report = {"milestone":"P0-S3 S7", "overall":"PASS" if all(checks.values()) else "FAIL",
              "checks":checks, "pytest_stdout":proc.stdout.strip(), "pytest_stderr":proc.stderr.strip()}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "s7_acceptance_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = ["P0-S3 S7 — Leakage & Invariant Test Suite Acceptance"]
    lines += [f"  {k}: {'PASS' if v else 'FAIL'}" for k,v in checks.items()]
    lines.append(f"OVERALL: {report['overall']}")
    summary = "\n".join(lines)
    (RESULTS / "s7_acceptance_summary.txt").write_text(summary + "\n", encoding="utf-8")
    print(summary)
    return 0 if report["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
