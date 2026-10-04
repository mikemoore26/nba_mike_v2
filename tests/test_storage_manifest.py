from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pytest
from nba_mike.storage import StorageManager


def test_tree(tmp_path):
    s=StorageManager(tmp_path); s.ensure_tree()
    for name in ("raw","validated","canonical","snapshots","features","targets","quarantine","manifests","cache"):
        assert (tmp_path/"data"/name).is_dir()

def test_register_roundtrip_and_verify(tmp_path):
    s=StorageManager(tmp_path)
    m=s.register_bytes(content=b"a,b\n1,2\n", source_name="NBA", dataset_name="player-game", extension="csv", request_parameters={"Season":"2025-26"})
    assert s.verify(m)
    loaded=s.read_manifest(m.artifact_id)
    assert loaded.sha256 == m.sha256 and loaded.request_parameters["Season"] == "2025-26"

def test_tamper_detection(tmp_path):
    s=StorageManager(tmp_path); m=s.register_bytes(content=b"truth",source_name="NBA",dataset_name="x",extension="txt")
    (tmp_path/m.relative_path).write_bytes(b"changed")
    assert not s.verify(m)

def test_quarantine_requires_reason_and_terminal_state(tmp_path):
    s=StorageManager(tmp_path); m=s.register_bytes(content=b"x",source_name="NBA",dataset_name="x",extension="txt")
    with pytest.raises(ValueError): s.set_validation(m.artifact_id,"QUARANTINED")
    q=s.set_validation(m.artifact_id,"QUARANTINED","schema mismatch")
    assert q.validation_status == "QUARANTINED"
    with pytest.raises(ValueError): s.set_validation(m.artifact_id,"PASS")

def test_cache_is_separate(tmp_path):
    s=StorageManager(tmp_path); s.ensure_tree()
    (tmp_path/"data"/"cache"/"throwaway.txt").write_text("cache")
    m=s.register_bytes(content=b"evidence",source_name="NBA",dataset_name="x",extension="bin")
    (tmp_path/"data"/"cache"/"throwaway.txt").unlink()
    assert s.verify(m)
