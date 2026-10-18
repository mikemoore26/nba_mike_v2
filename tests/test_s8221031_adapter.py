"""Offline tests of the production canonical-to-D1 adapter contract."""
import csv
import hashlib
import json

import pytest

from nba_mike.adapters.canonical_snapshot import (
    AdapterContractError, CANONICAL_COLUMNS, adapt_canonical_rows,
)


def fixture(tmp_path, *, mutate=None, target="2026-10-03"):
    rows = [
        dict(zip(CANONICAL_COLUMNS, ["g1", "2026-10-01", "p1", "t1", "t2", "30", "20", "5", "4", "2"])),
        dict(zip(CANONICAL_COLUMNS, ["g2", "2026-10-02", "p1", "t1", "t2", "32", "22", "6", "5", "3"])),
        dict(zip(CANONICAL_COLUMNS, ["g3", "2026-10-03", "p1", "t1", "t2", "34", "25", "7", "6", "4"])),
        dict(zip(CANONICAL_COLUMNS, ["g4", "2026-10-04", "p1", "t1", "t2", "35", "26", "8", "7", "5"])),
    ]
    if mutate:
        mutate(rows)
    csv_path = tmp_path / "canonical.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CANONICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    manifest = dict(artifact_id="test-canonical", sha256=hashlib.sha256(csv_path.read_bytes()).hexdigest(),
                    relative_path="canonical.csv", validation_status="PASS", layer="canonical",
                    dataset_name="player_game_box", row_count=len(rows))
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    args = dict(project_root=tmp_path, canonical_path=csv_path, canonical_manifest_path=manifest_path,
                target_game_date=target)
    return args, manifest_path, csv_path


def test_valid_snapshot_only_prior_dates(tmp_path):
    args, _, _ = fixture(tmp_path)
    rows, meta = adapt_canonical_rows(**args)
    assert [r["game_id"] for r in rows] == ["g1", "g2"]
    assert rows[0]["min"] == 30.0 and rows[0]["pts"] == 20.0
    assert "minutes" not in rows[0] and "game_date" not in rows[0]
    assert meta["contract"] == "D-1" and meta["row_count"] == 2
    assert meta["training_decision"] == "BLOCK_TRAINING"


def test_parent_tamper_rejected(tmp_path):
    args, _, artifact = fixture(tmp_path)
    artifact.write_bytes(artifact.read_bytes() + b"\n")
    with pytest.raises(AdapterContractError, match="PARENT_HASH_MISMATCH"):
        adapt_canonical_rows(**args)


def test_manifest_wrong_artifact_rejected(tmp_path):
    args, manifest_path, _ = fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text())
    manifest["relative_path"] = "another.csv"
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(AdapterContractError, match="MANIFEST_ARTIFACT_PATH_MISMATCH"):
        adapt_canonical_rows(**args)


def test_manifest_row_count_rejected(tmp_path):
    args, manifest_path, _ = fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text())
    manifest["row_count"] = 100
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(AdapterContractError, match="MANIFEST_ROW_COUNT_MISMATCH"):
        adapt_canonical_rows(**args)


@pytest.mark.parametrize("column,value,error", [
    ("minutes", "nan", "OUT_OF_RANGE"),
    ("minutes", "61", "OUT_OF_RANGE"),
    ("points", "-1", "OUT_OF_RANGE"),
    ("game_date", "2026-13-01", "INVALID_GAME_DATE"),
    ("team_id", "t2", "TEAM_EQUALS_OPPONENT"),
])
def test_invalid_data_rejected(tmp_path, column, value, error):
    args, _, _ = fixture(tmp_path, mutate=lambda rows: rows[0].__setitem__(column, value))
    with pytest.raises(AdapterContractError, match=error):
        adapt_canonical_rows(**args)


def test_duplicate_player_game_rejected(tmp_path):
    def mutate(rows):
        rows[1]["game_id"] = "g1"
    args, _, _ = fixture(tmp_path, mutate=mutate)
    with pytest.raises(AdapterContractError, match="DUPLICATE_KEY"):
        adapt_canonical_rows(**args)


def test_manifest_nonpass_rejected(tmp_path):
    args, manifest_path, _ = fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text())
    manifest["validation_status"] = "BLOCKED"
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(AdapterContractError, match="PARENT_NOT_VALIDATED"):
        adapt_canonical_rows(**args)


def test_outside_root_rejected(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    args, _, _ = fixture(tmp_path)
    args["project_root"] = root
    with pytest.raises(AdapterContractError, match="INPUT_OUTSIDE_PROJECT_ROOT"):
        adapt_canonical_rows(**args)
