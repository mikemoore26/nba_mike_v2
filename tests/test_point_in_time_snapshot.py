import hashlib
import json
from pathlib import Path

import pytest

from nba_mike.snapshots.builder import SnapshotError, build_d1_snapshot


def fixture(tmp_path: Path):
    p = tmp_path / "canonical.json"
    p.write_text('{"evidence":"canonical"}', encoding="utf-8")
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = {
        "artifact_id": "canonical-parent-001",
        "sha256": sha,
        "relative_path": "data/canonical/canonical.json",
        "validation_status": "PASS",
    }
    rows = [
        {"game_id":"g1","event_date":"2026-10-01","player_id":"p1","team_id":"t1","points":10},
        {"game_id":"g2","event_date":"2026-10-02","player_id":"p1","team_id":"t1","points":20},
        {"game_id":"g3","event_date":"2026-10-03","player_id":"p1","team_id":"t1","points":30},
        {"game_id":"g4","event_date":"2026-10-04","player_id":"p1","team_id":"t1","points":40},
    ]
    return p, manifest, rows


def test_d1_excludes_same_day_and_future(tmp_path):
    p,m,rows=fixture(tmp_path)
    out,meta=build_d1_snapshot(rows,target_game_date="2026-10-03",parent_manifest=m,parent_artifact_path=p)
    assert [r["game_id"] for r in out] == ["g1","g2"]
    assert meta["cutoff_date"] == "2026-10-02"


def test_explicit_as_of(tmp_path):
    p,m,rows=fixture(tmp_path)
    _,meta=build_d1_snapshot(rows,target_game_date="2026-10-03",parent_manifest=m,parent_artifact_path=p)
    assert meta["as_of_time"].startswith("2026-10-02T23:59:59")


def test_non_pass_parent_blocked(tmp_path):
    p,m,rows=fixture(tmp_path); m["validation_status"]="QUARANTINED"
    with pytest.raises(SnapshotError): build_d1_snapshot(rows,target_game_date="2026-10-03",parent_manifest=m,parent_artifact_path=p)


def test_tamper_rejected(tmp_path):
    p,m,rows=fixture(tmp_path); p.write_text("tampered",encoding="utf-8")
    with pytest.raises(SnapshotError): build_d1_snapshot(rows,target_game_date="2026-10-03",parent_manifest=m,parent_artifact_path=p)


def test_duplicate_rejected(tmp_path):
    p,m,rows=fixture(tmp_path); rows.append(dict(rows[0]))
    with pytest.raises(SnapshotError): build_d1_snapshot(rows,target_game_date="2026-10-03",parent_manifest=m,parent_artifact_path=p)


def test_deterministic_logical_snapshot(tmp_path):
    p,m,rows=fixture(tmp_path)
    a,ma=build_d1_snapshot(rows,target_game_date="2026-10-03",parent_manifest=m,parent_artifact_path=p)
    b,mb=build_d1_snapshot(list(reversed(rows)),target_game_date="2026-10-03",parent_manifest=m,parent_artifact_path=p)
    assert a == b
    assert ma["logical_sha256"] == mb["logical_sha256"]
    assert ma["snapshot_id"] == mb["snapshot_id"]


def test_zero_history_explicit(tmp_path):
    p,m,rows=fixture(tmp_path)
    _,meta=build_d1_snapshot(rows,target_game_date="2026-10-03",parent_manifest=m,parent_artifact_path=p,expected_entities=[{"player_id":"rookie","team_id":"t2"}])
    assert meta["entity_history"][0]["eligible_game_count"] == 0
    assert meta["entity_history"][0]["history_status"] == "ZERO_HISTORY"


def test_identity_preserved(tmp_path):
    p,m,rows=fixture(tmp_path)
    out,_=build_d1_snapshot(rows,target_game_date="2026-10-03",parent_manifest=m,parent_artifact_path=p)
    assert {(r["player_id"],r["team_id"]) for r in out} == {("p1","t1")}
