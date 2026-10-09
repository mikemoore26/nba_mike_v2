import csv
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_5/run_s8_5.py'
spec = importlib.util.spec_from_file_location('s85', MODULE_PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=m.COLUMNS)
        writer.writeheader(); writer.writerows(rows)


def record(game, day, mins='20', player='1'):
    return dict(game_id=game, event_date=day, player_id=player, team_id='2', min=mins, pts='10', reb='3', ast='4', fg3m='1')


def test_strict_prior_only(tmp_path):
    p = tmp_path / 'x.csv'
    write_rows(p, [record('1', '2020-01-01'), record('2', '2020-01-01'), record('3', '2020-01-02')])
    r = m.inspect(p, '2019-20')
    assert r['eligible_prior_history_rows'] == 1
    assert r['same_day_ambiguous_rows'] == 1
    assert r['examples'][0]['prior_game_count'] == 2


def test_duplicates_detected(tmp_path):
    p = tmp_path / 'x.csv'
    write_rows(p, [record('1', '2020-01-01'), record('1', '2020-01-01')])
    assert m.inspect(p, '2019-20')['duplicate_player_game_rows'] == 1


def test_invalid_target(tmp_path):
    p = tmp_path / 'x.csv'
    write_rows(p, [record('1', '2020-01-01', 'NaN')])
    assert m.inspect(p, '2019-20')['invalid_target_values'] == 1


def test_bad_date(tmp_path):
    p = tmp_path / 'x.csv'
    write_rows(p, [record('1', 'bad-date')])
    assert m.inspect(p, '2019-20')['invalid_date_rows'] == 1


def test_conflicting_game_dates(tmp_path):
    p = tmp_path / 'x.csv'
    write_rows(p, [record('1', '2020-01-01'), record('1', '2020-01-02', player='3')])
    assert m.inspect(p, '2019-20')['date_conflict_games'] == 1


def test_missing_file(tmp_path):
    assert m.inspect(tmp_path / 'missing.csv', '2019-20')['reason'] == 'MISSING_SNAPSHOT'


def test_missing_columns(tmp_path):
    p = tmp_path / 'x.csv'; p.write_text('player_id,game_id\n1,2\n')
    assert m.inspect(p, '2019-20')['reason'] == 'MISSING_REQUIRED_COLUMNS'


def test_no_training_promotion(tmp_path):
    for season in m.SEASONS:
        write_rows(tmp_path / 'research/p0_s4/s5_1/snapshots' / f'player_gamelogs_{season}.csv', [record('1', '2020-01-01')])
    r = m.run(tmp_path)
    assert r['decision'] == 'BLOCK_TRAINING'
    assert r['calendar_research_decision'] == 'PAUSE_ENDPOINT_RETRIES'
    assert 'min' in r['feature_policy']['forbidden_same_game_inputs']
