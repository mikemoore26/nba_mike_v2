import json
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nba_mike.identity import IdentityConflictError, IdentityRegistry


def base_registry():
    r = IdentityRegistry()
    nyk = r.create_team("New York Knicks")
    bos = r.create_team("Boston Celtics")
    p = r.create_player("Example Player")
    return r, nyk, bos, p


def test_stable_id_format_and_sequence():
    r = IdentityRegistry()
    assert r.create_player("A") == "P00000001"
    assert r.create_player("B") == "P00000002"
    assert r.create_team("T") == "T00000001"


def test_exact_source_mapping_resolves():
    r, _, _, p = base_registry()
    r.add_source_mapping("player", "nba_stats", "2544", p)
    got = r.resolve_source("player", "nba_stats", "2544")
    assert got.status == "RESOLVED" and got.canonical_id == p
    assert r.resolve_source("player", "nba_stats", "9999").status == "UNRESOLVED"


def test_source_remap_is_rejected():
    r = IdentityRegistry()
    p1 = r.create_player("A")
    p2 = r.create_player("B")
    r.add_source_mapping("player", "nba_stats", "7", p1)
    with pytest.raises(IdentityConflictError):
        r.add_source_mapping("player", "nba_stats", "7", p2)


def test_names_are_not_primary_keys_and_alias_can_be_ambiguous():
    r = IdentityRegistry()
    p1 = r.create_player("Same Name")
    p2 = r.create_player("Same Name")
    assert p1 != p2
    r.add_alias(p1, "Same Name")
    r.add_alias(p2, "Same Name")
    result = r.resolve_alias("player", "same   name")
    assert result.status == "AMBIGUOUS"
    assert set(result.candidates) == {p1, p2}


def test_trade_changes_membership_not_player_identity():
    r, nyk, bos, p = base_registry()
    r.add_membership(p, nyk, "2025-10-01", "2026-02-01", "transaction-test")
    r.add_membership(p, bos, "2026-02-01", None, "transaction-test")
    assert r.teams_for_player_on(p, "2026-01-15") == (nyk,)
    assert r.teams_for_player_on(p, "2026-02-15") == (bos,)
    assert p == "P00000001"


def test_game_integrity_and_source_mapping():
    r, nyk, bos, _ = base_registry()
    g = r.create_game("2026-10-20", nyk, bos)
    r.add_source_mapping("game", "nba_stats", "0022600001", g)
    assert r.resolve_source("game", "nba_stats", "0022600001").canonical_id == g
    with pytest.raises(ValueError):
        r.create_game("2026-10-21", nyk, nyk)


def test_player_game_duplicate_detection():
    rows = [{"game_id": "G1", "player_id": "P1"}, {"game_id": "G1", "player_id": "P2"}]
    IdentityRegistry.assert_unique_player_games(rows)
    with pytest.raises(IdentityConflictError):
        IdentityRegistry.assert_unique_player_games(rows + [{"game_id": "G1", "player_id": "P1"}])


def test_json_roundtrip_preserves_identity(tmp_path):
    r, nyk, bos, p = base_registry()
    g = r.create_game("2026-10-20", nyk, bos)
    r.add_source_mapping("player", "nba_stats", "123", p)
    r.add_source_mapping("game", "nba_stats", "0022600001", g)
    r.add_alias(p, "E. Player")
    r.add_membership(p, nyk, "2026-07-01", None, "test")
    path = tmp_path / "registry.json"
    r.save_json(path)
    loaded = IdentityRegistry.load_json(path)
    assert loaded.to_dict() == r.to_dict()
