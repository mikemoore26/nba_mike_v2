import importlib.util
from pathlib import Path
import csv
import pytest

MODULE = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_22_10_7/run_s8_22_10_7.py'
spec = importlib.util.spec_from_file_location('s822107', MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def schedule():
    return [{'game_date': d, 'pdf_matchup': match, 'external_status': 'CORROBORATED_ORIENTATION', 'record_count': '1'} for d, match in m.PROVISIONAL] + [
        {'game_date': '2023-11-16', 'pdf_matchup': 'BKN@MIA', 'external_status': 'CORROBORATED_ORIENTATION', 'record_count': '1'},
        {'game_date': '2023-11-16', 'pdf_matchup': 'OKC@GSW', 'external_status': 'CORROBORATED_ORIENTATION', 'record_count': '1'}]


def test_eight_provisional_ids_no_verified():
    x = m.reconcile(schedule())
    assert sum(bool(r['provisional_nba_game_id']) for r in x) == 8
    assert all(r['game_id_status'] != 'VERIFIED' for r in x)


def test_out_of_scope_games_no_ids():
    x = m.reconcile(schedule())
    assert all(not r['provisional_nba_game_id'] for r in x if r['game_date'] == '2023-11-16')


def test_duplicate_game_fails():
    with pytest.raises(ValueError, match='Duplicate'):
        m.reconcile(schedule() + schedule()[:1])


def test_missing_target_fails():
    with pytest.raises(ValueError, match='missing'):
        m.reconcile(schedule()[1:])


def test_uncorroborated_fails():
    s = schedule(); s[0]['external_status'] = 'UNKNOWN'
    with pytest.raises(ValueError, match='Uncorroborated'):
        m.reconcile(s)


def test_manual_reviews_always_pending():
    x = m.reconcile(schedule())
    rows = [{'record_id': f'P-{i}', 'game_date_candidate': row['game_date'], 'matchup_candidate': row['away_at_home'], 'manual_decision': 'PENDING', 'record_type': 'PLAYER'} for i, row in enumerate(x)]
    out = m.prepare_review(rows, x)
    assert len(out) == 10
    assert all(r['s822107_manual_decision'] == 'PENDING' and r['s822107_training_eligible'] == 'NO' for r in out)


def test_unknown_ledger_game_fails():
    x = m.reconcile(schedule())
    with pytest.raises(ValueError, match='missing from crosswalk'):
        m.prepare_review([{'record_id': 'P-1', 'game_date_candidate': '2023-11-17', 'matchup_candidate': 'AAA@BBB', 'manual_decision': 'PENDING'}], x)
