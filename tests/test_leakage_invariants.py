import pytest

from nba_mike.validation.invariants import (
    InvariantError,
    assert_d1_boundary,
    assert_entity_history_contract,
    assert_feature_target_separation,
    assert_snapshot_metadata,
    assert_team_opponent_consistency,
    assert_unique_keys,
)


def test_d1_boundary_accepts_only_prior_dates():
    assert_d1_boundary([
        {"event_date": "2026-10-01"},
        {"event_date": "2026-10-02"},
    ], target_game_date="2026-10-03")


def test_d1_boundary_rejects_target_day():
    with pytest.raises(InvariantError, match="D1_LEAKAGE"):
        assert_d1_boundary([{"event_date": "2026-10-03"}], target_game_date="2026-10-03")


def test_d1_boundary_rejects_future_day():
    with pytest.raises(InvariantError, match="D1_LEAKAGE"):
        assert_d1_boundary([{"event_date": "2026-10-04"}], target_game_date="2026-10-03")


def test_unique_player_game_key_rejects_duplicate():
    rows = [{"game_id":"g1","player_id":"p1"},{"game_id":"g1","player_id":"p1"}]
    with pytest.raises(InvariantError, match="DUPLICATE_KEY"):
        assert_unique_keys(rows)


def test_team_cannot_equal_opponent():
    with pytest.raises(InvariantError, match="TEAM_EQUALS_OPPONENT"):
        assert_team_opponent_consistency([{"team_id":"t1","opponent_team_id":"t1"}])


def test_feature_target_separation_rejects_outcome_column():
    features = [{"player_id":"p1","rolling_points_mean":22.5,"actual_points":31}]
    with pytest.raises(InvariantError, match="TARGET_LEAKAGE"):
        assert_feature_target_separation(features, forbidden_target_fields={"actual_points","target_over"})


def test_feature_target_separation_accepts_clean_features():
    assert_feature_target_separation(
        [{"player_id":"p1","rolling_points_mean":22.5}],
        forbidden_target_fields={"actual_points","target_over"},
    )


def test_snapshot_metadata_requires_d1_and_provenance():
    good = {
        "contract":"D-1", "target_game_date":"2026-10-03", "cutoff_date":"2026-10-02",
        "as_of_time":"2026-10-02T23:59:59+00:00", "parent_artifact_id":"a1",
        "parent_sha256":"abc", "logical_sha256":"def", "snapshot_id":"s1",
    }
    assert_snapshot_metadata(good, target_game_date="2026-10-03")
    bad = dict(good); bad.pop("parent_sha256")
    with pytest.raises(InvariantError, match="SNAPSHOT_PROVENANCE_MISSING"):
        assert_snapshot_metadata(bad, target_game_date="2026-10-03")


def test_zero_history_must_not_be_disguised_as_available():
    with pytest.raises(InvariantError, match="ENTITY_HISTORY_STATUS_INVALID"):
        assert_entity_history_contract({"entity_history":[{
            "player_id":"rookie", "team_id":"t2", "eligible_game_count":0,
            "history_status":"AVAILABLE",
        }]})
