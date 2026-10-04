from pathlib import Path
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest

from nba_mike.validation import (
    ColumnRule,
    ProvenanceError,
    SchemaContract,
    assert_parent_manifests_usable,
    validate_parent_chain,
    validate_records,
)


def player_game_contract() -> SchemaContract:
    return SchemaContract(
        name="canonical_player_game_v1",
        columns=(
            ColumnRule("game_id", (str,)),
            ColumnRule("player_id", (str,)),
            ColumnRule("team_id", (str,)),
            ColumnRule("minutes", (int, float), minimum=0, maximum=65),
            ColumnRule("points", (int,), minimum=0, maximum=100),
        ),
        primary_key=("game_id", "player_id"),
    )


def good_row():
    return {
        "game_id": "nba_game_1",
        "player_id": "nba_player_1",
        "team_id": "nba_team_1",
        "minutes": 34.5,
        "points": 27,
    }


def test_valid_record_passes():
    result = validate_records([good_row()], player_game_contract())
    assert result.passed
    assert result.validation_status == "PASS"


def test_missing_required_column_quarantines():
    row = good_row()
    del row["points"]
    result = validate_records([row], player_game_contract())
    assert not result.passed
    assert "MISSING_COLUMN" in result.issue_codes()
    assert result.validation_status == "QUARANTINED"


def test_extra_column_detects_schema_drift():
    row = good_row()
    row["surprise_field"] = 1
    result = validate_records([row], player_game_contract())
    assert "SCHEMA_DRIFT_EXTRA_COLUMN" in result.issue_codes()


def test_type_mismatch_detected():
    row = good_row()
    row["points"] = "27"
    result = validate_records([row], player_game_contract())
    assert "TYPE_MISMATCH" in result.issue_codes()


def test_impossible_value_detected():
    row = good_row()
    row["minutes"] = 90
    result = validate_records([row], player_game_contract())
    assert "VALUE_ABOVE_MAXIMUM" in result.issue_codes()


def test_duplicate_primary_key_detected():
    result = validate_records([good_row(), good_row()], player_game_contract())
    assert "DUPLICATE_PRIMARY_KEY" in result.issue_codes()


def test_non_pass_parent_rejected():
    with pytest.raises(ProvenanceError):
        assert_parent_manifests_usable([
            {"artifact_id": "raw-1", "validation_status": "QUARANTINED", "sha256": "abc"}
        ])


def test_parent_hash_verified(tmp_path):
    path = tmp_path / "raw.json"
    path.write_bytes(b'{"ok": true}')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {"artifact_id": "raw-1", "validation_status": "PASS", "sha256": digest}

    verified = validate_parent_chain([manifest], {"raw-1": path})
    assert verified["raw-1"] == digest


def test_parent_hash_tamper_rejected(tmp_path):
    path = tmp_path / "raw.json"
    path.write_bytes(b"tampered")
    manifest = {"artifact_id": "raw-1", "validation_status": "PASS", "sha256": "0" * 64}

    with pytest.raises(ProvenanceError):
        validate_parent_chain([manifest], {"raw-1": path})
