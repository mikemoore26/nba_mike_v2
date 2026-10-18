"""S8.22.10.30: offline cross-module integration, synthetic data only.

No API calls, model training, or real-world data are used by these tests.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nba_mike.canonical.builder import BuildError, build_player_game_box
from nba_mike.snapshots.builder import SnapshotError, build_d1_snapshot
from nba_mike.validation.invariants import (
    InvariantError, assert_d1_boundary, assert_entity_history_contract,
    assert_feature_target_separation, assert_snapshot_metadata,
    assert_team_opponent_consistency, assert_unique_keys,
)
from nba_mike.validation.provenance import ProvenanceError, validate_parent_chain
from nba_mike.features.opportunity import build_opportunity_research_frame

FIELDS = ("GAME_ID", "GAME_DATE", "PLAYER_ID", "TEAM_ID", "OPP_TEAM_ID", "MIN", "PTS", "REB", "AST", "FG3M")
COLUMN_MAP = dict(zip(("game_id", "game_date", "player_id", "team_id", "opponent_team_id", "minutes", "points", "rebounds", "assists", "three_pointers_made"), FIELDS))
IDS = {
    ("player", "synthetic", "1"): "player-1",
    ("player", "synthetic", "2"): "player-2",
    ("team", "synthetic", "10"): "team-10",
    ("team", "synthetic", "20"): "team-20",
}


def game(gid, date, player="1", minutes="20", pts="10"):
    return dict(zip(FIELDS, (gid, date, player, "10", "20", minutes, pts, "4", "2", "1")))


def raw_fixture(tmp_path, rows):
    raw = tmp_path / "raw.csv"
    with raw.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    manifest = tmp_path / "raw.manifest.json"
    manifest.write_text(json.dumps({"artifact_id": "synthetic-raw", "sha256": hashlib.sha256(raw.read_bytes()).hexdigest(), "validation_status": "PASS"}), encoding="utf-8")
    return raw, manifest


def canonical_fixture(tmp_path, rows, ids=IDS):
    raw, parent = raw_fixture(tmp_path, rows)
    result = build_player_game_box(
        project_root=tmp_path, raw_path=raw, parent_manifest_path=parent,
        output_path=tmp_path / "canonical.csv", output_manifest_path=tmp_path / "canonical.manifest.json",
        source_name="synthetic", column_map=COLUMN_MAP, identity_resolver=ids,
    )
    return raw, parent, result


def snapshot_fixture(tmp_path, rows, target="2026-10-24"):
    _, _, built = canonical_fixture(tmp_path, rows)
    parent = json.loads(built.manifest_path.read_text(encoding="utf-8"))
    with built.output_path.open(newline="", encoding="utf-8") as f:
        canonical_rows = list(csv.DictReader(f))
    # Explicit interface adapter: canonical.game_date -> snapshot.event_date.
    adapted = [{**r, "event_date": r["game_date"]} for r in canonical_rows]
    eligible, metadata = build_d1_snapshot(
        adapted, target_game_date=target, parent_manifest=parent,
        parent_artifact_path=built.output_path,
        expected_entities=[{"player_id": "player-1", "team_id": "team-10"},
                           {"player_id": "player-2", "team_id": "team-10"}],
    )
    return built, parent, eligible, metadata


def feature_adapter(rows):
    """Explicit research adapter; never use post-target outcomes to form features."""
    rename = {"minutes": "min", "points": "pts", "rebounds": "reb", "assists": "ast", "three_pointers_made": "fg3m"}
    frame = pd.DataFrame(rows).rename(columns=rename)
    return build_opportunity_research_frame(frame)


def test_cross_module_happy_path(tmp_path):
    built, parent, eligible, metadata = snapshot_fixture(tmp_path, [
        game("g1", "2026-10-20", minutes="20"),
        game("g2", "2026-10-22", minutes="30"),
        game("g3", "2026-10-24", minutes="60"),  # target-day outcome MUST be excluded
    ])
    assert built.row_count == 3
    assert len(eligible) == 2
    assert {r["game_id"] for r in eligible} == {"g1", "g2"}
    validate_parent_chain([parent], {parent["artifact_id"]: built.output_path})
    assert_d1_boundary(eligible, target_game_date="2026-10-24")
    assert_unique_keys(eligible)
    assert_team_opponent_consistency(eligible)
    assert_snapshot_metadata(metadata, target_game_date="2026-10-24")
    assert_entity_history_contract(metadata)
    assert metadata["entity_history"][0]["eligible_game_count"] == 2
    assert metadata["entity_history"][1]["history_status"] == "ZERO_HISTORY"
    feature_frame = feature_adapter(eligible)
    assert feature_frame["game_id"].tolist() == ["g1", "g2"]
    assert pd.isna(feature_frame.loc[0, "minutes_last3_avg"])
    assert feature_frame.loc[1, "minutes_last3_avg"] == pytest.approx(20)
    # Research frame includes realized target_minutes for evaluation. Strip it
    # before asserting that a pregame feature-only record is clean.
    feature_only = feature_frame.drop(columns=["target_minutes"])
    assert_feature_target_separation(feature_only.to_dict("records"), forbidden_target_fields={"target_minutes", "actual_points"})


def test_tampered_raw_parent_fails_closed(tmp_path):
    raw, parent = raw_fixture(tmp_path, [game("g1", "2026-10-20")])
    raw.write_bytes(raw.read_bytes() + b"\ncorruption")
    with pytest.raises(BuildError, match="PARENT_HASH_MISMATCH"):
        build_player_game_box(project_root=tmp_path, raw_path=raw, parent_manifest_path=parent,
                              output_path=tmp_path / "canonical.csv", output_manifest_path=tmp_path / "canonical.manifest.json",
                              source_name="synthetic", column_map=COLUMN_MAP, identity_resolver=IDS)
    assert not (tmp_path / "canonical.csv").exists()


def test_unresolved_player_identity_fails_closed(tmp_path):
    raw, parent = raw_fixture(tmp_path, [game("g1", "2026-10-20", player="999")])
    with pytest.raises(BuildError, match="IDENTITY_UNRESOLVED"):
        build_player_game_box(project_root=tmp_path, raw_path=raw, parent_manifest_path=parent,
                              output_path=tmp_path / "canonical.csv", output_manifest_path=tmp_path / "canonical.manifest.json",
                              source_name="synthetic", column_map=COLUMN_MAP, identity_resolver=IDS)


def test_tampered_canonical_parent_rejected_by_snapshot(tmp_path):
    built, parent, eligible, metadata = snapshot_fixture(tmp_path, [game("g1", "2026-10-20")])
    built.output_path.write_bytes(built.output_path.read_bytes() + b"\ncorruption")
    with pytest.raises(ProvenanceError):
        validate_parent_chain([parent], {parent["artifact_id"]: built.output_path})
    with pytest.raises(SnapshotError, match="SHA-256"):
        build_d1_snapshot(eligible, target_game_date="2026-10-24", parent_manifest=parent,
                          parent_artifact_path=built.output_path)


def test_target_day_and_future_rows_never_enter_snapshot(tmp_path):
    _, _, eligible, metadata = snapshot_fixture(tmp_path, [
        game("g1", "2026-10-23"), game("g2", "2026-10-24"), game("g3", "2026-10-25")
    ])
    assert [r["game_id"] for r in eligible] == ["g1"]
    assert metadata["cutoff_date"] == "2026-10-23"
    with pytest.raises(InvariantError, match="D1_LEAKAGE"):
        assert_d1_boundary([{"event_date": "2026-10-24"}], target_game_date="2026-10-24")


def test_feature_target_separation_fails_closed(tmp_path):
    _, _, eligible, _ = snapshot_fixture(tmp_path, [game("g1", "2026-10-20")])
    frame = feature_adapter(eligible)
    with pytest.raises(InvariantError, match="TARGET_LEAKAGE"):
        assert_feature_target_separation(frame.to_dict("records"), forbidden_target_fields={"target_minutes"})


def test_same_day_doubleheader_has_no_cross_game_leakage(tmp_path):
    _, _, eligible, _ = snapshot_fixture(tmp_path, [
        game("g1", "2026-10-20", minutes="20"),
        game("g2", "2026-10-22", minutes="30"),
        game("g3", "2026-10-22", minutes="40"),
    ])
    frame = feature_adapter(eligible)
    day2 = frame.loc[frame["event_date"] == pd.Timestamp("2026-10-22")]
    assert len(day2) == 2
    assert day2["minutes_last3_avg"].tolist() == pytest.approx([20, 20])
    assert day2["prior_games"].tolist() == [1, 1]
