import csv
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_1/run_s8_1.py'
spec = importlib.util.spec_from_file_location('s81', MODULE_PATH)
s81 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s81)


def write(path, rows, columns=('PLAYER_ID', 'GAME_ID', 'GAME_DATE', 'MIN', 'PTS', 'REB')):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


def row(**overrides):
    base = dict(PLAYER_ID='1', GAME_ID='0021900001', GAME_DATE='2019-10-22', MIN='30:30', PTS='20', REB='4')
    base.update(overrides)
    return base


def test_minutes_clock(): assert s81.parse_minutes('30:30') == 30.5

def test_minutes_decimal(): assert s81.parse_minutes('30.5') == 30.5

def test_minutes_invalid_seconds(): assert s81.parse_minutes('30:60') is None

def test_minutes_blank(): assert s81.parse_minutes('') is None

def test_minutes_invalid(): assert s81.parse_minutes('abc') is None

def test_date_iso(): assert str(s81.parse_date('2019-10-22')) == '2019-10-22'

def test_date_invalid(): assert s81.parse_date('not-date') is None

def test_missing_file(tmp_path): assert s81.audit_file(tmp_path / 'missing.csv', '2019-20')['issues']['MISSING_FILE'] == 1

def test_clean(tmp_path):
    p = tmp_path / 'a.csv'; write(p, [row()]); r = s81.audit_file(p, '2019-20')
    assert r['row_count'] == 1 and r['issues'] == {} and not r['training_eligible']

def test_duplicate(tmp_path):
    p = tmp_path / 'a.csv'; write(p, [row(), row()])
    assert s81.audit_file(p, '2019-20')['issues']['DUPLICATE_PLAYER_GAME'] == 1

def test_missing_player(tmp_path):
    p = tmp_path / 'a.csv'; write(p, [row(PLAYER_ID='')])
    assert s81.audit_file(p, '2019-20')['issues']['MISSING_PLAYER_ID'] == 1

def test_out_of_season(tmp_path):
    p = tmp_path / 'a.csv'; write(p, [row(GAME_DATE='2023-10-22')])
    assert s81.audit_file(p, '2019-20')['issues']['DATE_OUTSIDE_BROAD_SEASON_WINDOW'] == 1

def test_bad_minutes(tmp_path):
    p = tmp_path / 'a.csv'; write(p, [row(MIN='90')])
    assert s81.audit_file(p, '2019-20')['issues']['MINUTES_OUTSIDE_PLAUSIBLE_RANGE'] == 1

def test_negative_points(tmp_path):
    p = tmp_path / 'a.csv'; write(p, [row(PTS='-2')])
    assert s81.audit_file(p, '2019-20')['issues']['NEGATIVE_PTS'] == 1

def test_missing_column(tmp_path):
    p = tmp_path / 'a.csv'; write(p, [{'PLAYER_ID': '1', 'GAME_ID': '1', 'GAME_DATE': '2019-10-22', 'PTS': '2'}], columns=('PLAYER_ID', 'GAME_ID', 'GAME_DATE', 'PTS'))
    assert s81.audit_file(p, '2019-20')['issues']['MISSING_MINUTES_COLUMN'] == 1

def test_outputs(tmp_path):
    base = tmp_path / 'research/p0_s4/s5_1/snapshots'
    for season in s81.SEASONS:
        write(base / f'player_gamelogs_{season}.csv', [row(GAME_DATE=f'{season[:4]}-10-22')])
    report = s81.audit(tmp_path, tmp_path / 'out')
    assert report['total_rows_scanned'] == 3 and not report['training_eligible']
    assert (tmp_path / 'out/s8_1_schema_review.csv').exists()

def test_limit(tmp_path):
    p = tmp_path / 'a.csv'; write(p, [row(), row(GAME_ID='2')])
    r = s81.audit_file(p, '2019-20', max_rows=1)
    assert r['row_count'] == 1 and r['issues']['ROW_SCAN_LIMIT_REACHED'] == 1
