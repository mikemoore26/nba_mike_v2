"""S8.1 offline game-log quality audit; never trains or certifies as-of provenance."""
import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

SEASONS = ('2019-20', '2023-24', '2025-26')
TARGETS = ('PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'PLUS_MINUS')
PLAYER_KEYS = ('PLAYER_ID', 'PERSON_ID', 'player_id', 'personId')
GAME_KEYS = ('GAME_ID', 'game_id', 'gameId')
DATE_KEYS = ('GAME_DATE', 'game_date', 'gameDate', 'event_date', 'EVENT_DATE', 'date')
MIN_KEYS = ('MIN', 'MINUTES', 'minutes', 'min')
SEASON_KEYS = ('SEASON', 'season', 'SEASON_ID')
MAX_ROWS = 2_000_000


def choose(columns, candidates):
    for item in candidates:
        if item in columns:
            return item
    return ''


def parse_minutes(value):
    value = str(value or '').strip()
    if not value:
        return None
    try:
        if ':' in value:
            parts = value.split(':')
            if len(parts) != 2:
                return None
            m, s = map(float, parts)
            if m < 0 or not 0 <= s < 60:
                return None
            return m + s / 60
        return float(value)
    except ValueError:
        return None


def parse_date(value):
    value = str(value or '').strip()
    if not value:
        return None
    for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%b %d, %Y', '%b %d %Y', '%m/%d/%Y', '%Y%m%d'):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None


def season_bounds(season):
    first = int(season[:4])
    return datetime(first, 7, 1).date(), datetime(first + 1, 7, 1).date()


def audit_file(path, season, max_rows=MAX_ROWS):
    result = {'season': season, 'path': str(path), 'exists': path.is_file(), 'status': 'BLOCKED',
              'row_count': 0, 'issues': {}, 'columns': [], 'column_map': {}, 'sha256': '',
              'date_min': None, 'date_max': None, 'unique_players': 0, 'unique_games': 0,
              'asof_provenance_verified': False, 'training_eligible': False}
    if not path.is_file():
        result['issues'] = {'MISSING_FILE': 1}
        return result
    h = hashlib.sha256()
    with path.open('rb') as raw:
        for chunk in iter(lambda: raw.read(1024 * 1024), b''):
            h.update(chunk)
    result['sha256'] = h.hexdigest()
    issues = Counter()
    players, games, keys = set(), set(), set()
    dates = []
    lo, hi = season_bounds(season)
    try:
        with path.open('r', encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            cols = reader.fieldnames or []
            result['columns'] = cols
            if len(cols) != len(set(cols)):
                issues['DUPLICATE_COLUMN_NAME'] += 1
            mapping = {'player': choose(cols, PLAYER_KEYS), 'game': choose(cols, GAME_KEYS),
                       'date': choose(cols, DATE_KEYS), 'minutes': choose(cols, MIN_KEYS),
                       'season': choose(cols, SEASON_KEYS)}
            result['column_map'] = mapping
            for k in ('player', 'game', 'date', 'minutes'):
                if not mapping[k]:
                    issues['MISSING_' + k.upper() + '_COLUMN'] += 1
            available_targets = [c for c in cols if c.upper() in TARGETS]
            result['available_targets'] = available_targets
            if not available_targets:
                issues['NO_STAT_TARGET_COLUMNS'] += 1
            for i, row in enumerate(reader):
                if i >= max_rows:
                    issues['ROW_SCAN_LIMIT_REACHED'] += 1
                    break
                result['row_count'] += 1
                if None in row:
                    issues['EXTRA_FIELDS_IN_ROW'] += 1
                player = (row.get(mapping['player']) or '').strip() if mapping['player'] else ''
                game = (row.get(mapping['game']) or '').strip() if mapping['game'] else ''
                if mapping['player'] and not player:
                    issues['MISSING_PLAYER_ID'] += 1
                if mapping['game'] and not game:
                    issues['MISSING_GAME_ID'] += 1
                if player and game:
                    key = (player, game)
                    if key in keys:
                        issues['DUPLICATE_PLAYER_GAME'] += 1
                    keys.add(key)
                    players.add(player)
                    games.add(game)
                if mapping['date']:
                    val = (row.get(mapping['date']) or '').strip()
                    day = parse_date(val)
                    if day is None:
                        issues['MISSING_OR_INVALID_DATE'] += 1
                    else:
                        dates.append(day)
                        if not lo <= day < hi:
                            issues['DATE_OUTSIDE_BROAD_SEASON_WINDOW'] += 1
                if mapping['minutes']:
                    val = (row.get(mapping['minutes']) or '').strip()
                    minute = parse_minutes(val)
                    if minute is None:
                        issues['MISSING_OR_INVALID_MINUTES'] += 1
                    elif not 0 <= minute <= 75:
                        issues['MINUTES_OUTSIDE_PLAUSIBLE_RANGE'] += 1
                for col in available_targets:
                    val = (row.get(col) or '').strip()
                    if not val:
                        issues['MISSING_' + col.upper()] += 1
                        continue
                    try:
                        number = float(val)
                    except ValueError:
                        issues['NONNUMERIC_' + col.upper()] += 1
                        continue
                    if not math.isfinite(number):
                        issues['NONFINITE_' + col.upper()] += 1
                        continue
                    if not -1000 <= number <= 1000:
                        issues['EXTREME_' + col.upper()] += 1
                    if number < 0 and col.upper() != 'PLUS_MINUS':
                        issues['NEGATIVE_' + col.upper()] += 1
            result['unique_players'] = len(players)
            result['unique_games'] = len(games)
            result['date_min'] = min(dates).isoformat() if dates else None
            result['date_max'] = max(dates).isoformat() if dates else None
            if result['row_count'] == 0:
                issues['EMPTY_DATASET'] += 1
    except (UnicodeError, csv.Error, OSError) as exc:
        issues['READ_ERROR'] += 1
        result['read_error_type'] = type(exc).__name__
    result['issues'] = dict(sorted(issues.items()))
    result['status'] = 'NEEDS_REPAIR' if issues else 'QUALITY_CHECKS_PASS_ASOF_UNVERIFIED'
    return result


def audit(root, output, max_rows=MAX_ROWS):
    base = root / 'research/p0_s4/s5_1/snapshots'
    entries = [audit_file(base / f'player_gamelogs_{season}.csv', season, max_rows) for season in SEASONS]
    schema = {e['season']: e['columns'] for e in entries}
    common = sorted(set.intersection(*(set(cols) for cols in schema.values()))) if all(schema.values()) else []
    union = sorted(set().union(*(set(cols) for cols in schema.values())))
    report = {'milestone': 'S8.2', 'mode': 'SCHEMA_RECOGNITION_REPAIR_REAUDIT', 'status': 'RESEARCH_ONLY',
              'decision': 'BLOCK_TRAINING', 'training_eligible': False,
              'historical_roster_transaction_features': 'BLOCKED_S7_51',
              'recognition_repair': {'date_aliases_added': ['event_date', 'EVENT_DATE'], 'target_matching': 'case_insensitive', 'source_snapshots_modified': False},
              'dataset_count': len(entries), 'total_rows_scanned': sum(e['row_count'] for e in entries),
              'schema_common_columns': common, 'schema_union_columns': union,
              'datasets': entries, 'limitations': [
                  'Postgame targets are outcomes, never same-game pregame features',
                  'No pre-tipoff publication or historical feature as-of provenance established',
                  'Broad season window is a sanity check, not a full schedule or completeness audit',
                  'No DNP completeness, opponent matchup, odds, injury or roster certification',
                  'No model training, betting recommendation, or deployment approval',
                  'Audit status indicates data quality only, never as-of certification']}
    output.mkdir(parents=True, exist_ok=True)
    (output / 's8_2_report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    with (output / 's8_2_dataset_review.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['season', 'path', 'status', 'row_count', 'unique_players', 'unique_games', 'date_min', 'date_max', 'issue_total', 'issues', 'sha256', 'training_eligible'])
        writer.writeheader()
        for e in entries:
            writer.writerow({k: (sum(e['issues'].values()) if k == 'issue_total' else json.dumps(e['issues'], sort_keys=True) if k == 'issues' else e.get(k, '')) for k in writer.fieldnames})
    with (output / 's8_2_schema_review.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['column', *SEASONS, 'classification'])
        writer.writeheader()
        for col in union:
            writer.writerow({'column': col, **{s: col in schema[s] for s in SEASONS},
                             'classification': 'POSTGAME_OUTCOME_OR_IDENTITY_REVIEW' if col.upper() in TARGETS or col.upper() in ('MIN', 'MINUTES') else 'ASOF_NOT_VERIFIED'})
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', type=Path, default=Path('.'))
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--max-rows', type=int, default=MAX_ROWS)
    args = parser.parse_args()
    if args.max_rows < 1:
        parser.error('--max-rows must be >= 1')
    root = args.project_root.resolve()
    output = args.output_dir or root / 'research/p0_s8/s8_2/results'
    report = audit(root, output, args.max_rows)
    print(json.dumps({'milestone': report['milestone'], 'decision': report['decision'], 'total_rows_scanned': report['total_rows_scanned'], 'datasets': [{'season': d['season'], 'rows': d['row_count'], 'status': d['status'], 'issues': d['issues']} for d in report['datasets']]}, indent=2))


if __name__ == '__main__':
    main()
