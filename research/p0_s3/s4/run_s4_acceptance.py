from __future__ import annotations

from pathlib import Path
import hashlib
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nba_mike.validation import (
    ColumnRule,
    ProvenanceError,
    SchemaContract,
    validate_parent_chain,
    validate_records,
)


def contract():
    return SchemaContract(
        name="acceptance_player_game_v1",
        columns=(
            ColumnRule("game_id", (str,)),
            ColumnRule("player_id", (str,)),
            ColumnRule("team_id", (str,)),
            ColumnRule("minutes", (int, float), minimum=0, maximum=65),
            ColumnRule("points", (int,), minimum=0, maximum=100),
        ),
        primary_key=("game_id", "player_id"),
    )


def base_row():
    return {
        "game_id": "game-1",
        "player_id": "player-1",
        "team_id": "team-1",
        "minutes": 35.0,
        "points": 24,
    }


def main() -> int:
    checks = {}

    checks["valid_schema"] = validate_records([base_row()], contract()).passed

    missing = base_row()
    missing.pop("points")
    checks["missing_required_rejected"] = (
        "MISSING_COLUMN" in validate_records([missing], contract()).issue_codes()
    )

    drift = base_row()
    drift["new_unapproved_field"] = "x"
    checks["schema_drift_rejected"] = (
        "SCHEMA_DRIFT_EXTRA_COLUMN" in validate_records([drift], contract()).issue_codes()
    )

    impossible = base_row()
    impossible["minutes"] = 99
    checks["impossible_value_rejected"] = (
        "VALUE_ABOVE_MAXIMUM" in validate_records([impossible], contract()).issue_codes()
    )

    checks["duplicate_key_rejected"] = (
        "DUPLICATE_PRIMARY_KEY"
        in validate_records([base_row(), base_row()], contract()).issue_codes()
    )

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "parent.json"
        path.write_bytes(b'{"source": "acceptance"}')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        parent = {"artifact_id": "raw-acceptance", "validation_status": "PASS", "sha256": digest}

        try:
            validate_parent_chain([parent], {"raw-acceptance": path})
            checks["parent_hash_verified"] = True
        except ProvenanceError:
            checks["parent_hash_verified"] = False

        path.write_bytes(b"tampered")
        try:
            validate_parent_chain([parent], {"raw-acceptance": path})
            checks["tamper_rejected"] = False
        except ProvenanceError:
            checks["tamper_rejected"] = True

    try:
        validate_parent_chain(
            [{"artifact_id": "bad", "validation_status": "QUARANTINED", "sha256": "x"}],
            {"bad": __file__},
        )
        checks["quarantined_parent_blocked"] = False
    except ProvenanceError:
        checks["quarantined_parent_blocked"] = True

    overall = all(checks.values())

    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "milestone": "P0-S3 S4",
        "name": "Schema Validation & Provenance Enforcement",
        "checks": checks,
        "overall": "PASS" if overall else "FAIL",
    }
    (results_dir / "s4_acceptance_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    lines = ["P0-S3 S4 — Schema Validation & Provenance Enforcement"]
    for name, passed in checks.items():
        lines.append(f"  {name}: {'PASS' if passed else 'FAIL'}")
    lines.append(f"OVERALL: {'PASS' if overall else 'FAIL'}")
    summary = "\n".join(lines) + "\n"
    (results_dir / "s4_acceptance_summary.txt").write_text(summary, encoding="utf-8")
    print(summary, end="")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
