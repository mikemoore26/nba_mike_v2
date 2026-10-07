from nba_mike.reconstruction import (
    HistoricalReconstructionError,
    canonicalize_player_game_rows,
    choose_representative_target_date,
    reconstruct_d1_rows,
    summarize_target_date_delta,
)


ROWS = [
    {"GAME_ID": "1", "GAME_DATE": "2025-10-20", "PLAYER_ID": 10, "TEAM_ID": 100},
    {"GAME_ID": "1", "GAME_DATE": "2025-10-20", "PLAYER_ID": 11, "TEAM_ID": 100},
    {"GAME_ID": "2", "GAME_DATE": "2025-10-22", "PLAYER_ID": 10, "TEAM_ID": 100},
    {"GAME_ID": "2", "GAME_DATE": "2025-10-22", "PLAYER_ID": 12, "TEAM_ID": 100},
    {"GAME_ID": "3", "GAME_DATE": "2025-10-24", "PLAYER_ID": 10, "TEAM_ID": 100},
    {"GAME_ID": "3", "GAME_DATE": "2025-10-24", "PLAYER_ID": 12, "TEAM_ID": 100},
]


def test_canonicalize_is_deterministic():
    assert canonicalize_player_game_rows(ROWS) == canonicalize_player_game_rows(list(reversed(ROWS)))


def test_duplicate_player_game_rejected():
    try:
        canonicalize_player_game_rows(ROWS + [ROWS[0]])
    except HistoricalReconstructionError:
        return
    raise AssertionError("duplicate row was not rejected")


def test_d1_excludes_target_and_future():
    rebuilt = reconstruct_d1_rows(ROWS, "2025-10-22")
    assert {r["event_date"] for r in rebuilt} == {"2025-10-20"}


def test_target_delta_contract():
    result = summarize_target_date_delta(ROWS, "2025-10-22")
    assert result["pass"] is True
    assert result["wrong_target_player_deltas"] == []
    assert result["wrong_non_target_player_deltas"] == []


def test_representative_date_is_deterministic_and_internal():
    chosen = choose_representative_target_date(ROWS)
    assert chosen == "2025-10-22"
