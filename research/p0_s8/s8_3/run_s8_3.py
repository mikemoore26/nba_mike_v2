"""S8.3: offline 2019-20 calendar exception audit, never a schedule certification."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

SEASONS = ('2019-20', '2023-24', '2025-26')
# Research windows are not a substitute for independent official game-level schedule evidence.
WINDOWS = {
    '2019-20': (date(2019, 10, 22), date(2020, 8, 14)),
    '2023-24': (date(2023, 10, 24), date(2024, 4, 14)),
    '2025-26': (date(2025, 10, 21), date(2026, 4, 12)),
}
BUBBLE_START = date(2020, 7, 30)
BUBBLE_END = date(2020, 8, 14)
OLD_BOUNDARY = date(2020, 7, 1)


def parse_iso_date(raw):
    try:
        return date.fromisoformat(str(raw).strip()[:10]) if raw else None
    except ValueError:
        return None


def classify(season, day):
    if day is None:
        return 'INVALID_DATE'
    if season == '2019-20' and BUBBLE_START <= day <= BUBBLE_END:
        return 'BUBBLE_RESTART_CANDIDATE_UNVERIFIED'
    if season == '2019-20' and OLD_BOUNDARY <= day < BUBBLE_START:
        return 'JULY_PRE_RESTART_REQUIRES_REVIEW'
    lo, hi = WINDOWS[season]
    if lo <= day <= hi:
        return 'IN_RESEARCH_WINDOW_NOT_SCHEDULE_VERIFIED'
    return 'OUTSIDE_RESEARCH_WINDOW_REQUIRES_REVIEW'


def inspect(path, season, detail_rows):
    summary = {'season': season, 'path': str(path), 'exists': path.is_file(), 'rows': 0,
               'unique_games': 0, 'old_window_flag_rows': 0, 'old_window_flag_games': 0,
               'classification_counts': {}, 'date_game_conflicts': 0,
               'duplicate_player_game': 0, 'sha256': '', 'read_error': None}
    if not path.is_file():
        summary['read_error'] = 'MISSING_FILE'
        return summary
    summary['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    counts = Counter()
    game_dates = defaultdict(set)
    old_games = set()
    keys = set()
    per_game = {}
    try:
        with path.open('r', encoding='utf-8-sig', newline='') as fh:
            reader = csv.DictReader(fh)
            needed = {'game_id', 'event_date', 'player_id'}
            if not needed.issubset(reader.fieldnames or []):
                summary['read_error'] = 'MISSING_REQUIRED_COLUMNS'
                return summary
            for row in reader:
                summary['rows'] += 1
                game = str(row.get('game_id') or '').strip()
                player = str(row.get('player_id') or '').strip()
                raw_date = str(row.get('event_date') or '').strip()
                day = parse_iso_date(raw_date)
                category = classify(season, day)
                counts[category] += 1
                if game:
                    game_dates[game].add(day.isoformat() if day else 'INVALID')
                key = (game, player)
                if game and player:
                    if key in keys:
                        summary['duplicate_player_game'] += 1
                    keys.add(key)
                if season == '2019-20' and day is not None and day >= OLD_BOUNDARY:
                    summary['old_window_flag_rows'] += 1
                    old_games.add(game)
                # One output per season, date, game, classification (no player-level PII).
                detail_key = (season, raw_date, game, category)
                if detail_key not in per_game:
                    per_game[detail_key] = {'season': season, 'event_date': raw_date,
                                            'game_id': game, 'classification': category,
                                            'player_rows': 0, 'schedule_verified': False,
                                            'training_eligible': False}
                per_game[detail_key]['player_rows'] += 1
    except (OSError, UnicodeError, csv.Error) as exc:
        summary['read_error'] = type(exc).__name__
    summary['classification_counts'] = dict(sorted(counts.items()))
    summary['unique_games'] = len(game_dates)
    summary['old_window_flag_games'] = len(old_games)
    summary['date_game_conflicts'] = sum(len(days) > 1 for days in game_dates.values())
    detail_rows.extend(per_game.values())
    return summary


def run(root, output):
    root = Path(root)
    detail = []
    base = root / 'research/p0_s4/s5_1/snapshots'
    datasets = [inspect(base / f'player_gamelogs_{s}.csv', s, detail) for s in SEASONS]
    old = datasets[0]
    remaining = (old['classification_counts'].get('JULY_PRE_RESTART_REQUIRES_REVIEW', 0)
                 + old['classification_counts'].get('OUTSIDE_RESEARCH_WINDOW_REQUIRES_REVIEW', 0)
                 + old['classification_counts'].get('INVALID_DATE', 0))
    report = {
        'milestone': 'S8.3', 'mode': 'OFFLINE_CALENDAR_EXCEPTION_AUDIT',
        'status': 'RESEARCH_ONLY', 'decision': 'BLOCK_TRAINING',
        'training_eligible': False, 'historical_roster_transaction_features': 'BLOCKED_S7_51',
        'old_rule': '2019-20 date >= 2020-07-01 flagged by S8.2 broad season window',
        'candidate_restart_window': ['2020-07-30', '2020-08-14'],
        'candidate_restart_status': 'PLAUSIBLE_NOT_INDEPENDENTLY_GAME_VERIFIED',
        's8_2_flagged_rows_expected': 1892,
        's8_2_flagged_rows_observed': old['old_window_flag_rows'],
        's8_2_flag_count_matches': old['old_window_flag_rows'] == 1892,
        '2019_20_unresolved_calendar_rows': remaining,
        'datasets': datasets,
        'next_gate': 'Independent official schedule game_id/date crosscheck before labeling bubble games verified',
        'limitations': [
            'The candidate restart window is historical context, not a validated game-ID schedule.',
            'All outcomes remain postgame-only; no same-game target may be used as a pregame feature.',
            'No season is certified for training, betting, historical roster, or injury features.',
            'Research windows do not establish schedule completeness or pre-tipoff publication.',
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / 's8_3_report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    fields = ['season', 'event_date', 'game_id', 'classification', 'player_rows', 'schedule_verified', 'training_eligible']
    with (output / 's8_3_game_calendar_review.csv').open('w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(sorted(detail, key=lambda x: (x['season'], x['event_date'], x['game_id'])))
    fields2 = ['season', 'rows', 'unique_games', 'old_window_flag_rows', 'old_window_flag_games', 'date_game_conflicts', 'duplicate_player_game', 'classification_counts', 'sha256', 'read_error']
    with (output / 's8_3_dataset_review.csv').open('w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=fields2)
        w.writeheader()
        for d in datasets:
            w.writerow({k: json.dumps(d[k], sort_keys=True) if k == 'classification_counts' else d.get(k) for k in fields2})
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root', type=Path, default=Path('.'))
    p.add_argument('--output-dir', type=Path)
    args = p.parse_args()
    root = args.project_root.resolve()
    report = run(root, args.output_dir or root / 'research/p0_s8/s8_3/results')
    print(json.dumps({'milestone': report['milestone'], 'decision': report['decision'],
                      'old_flags_observed': report['s8_2_flagged_rows_observed'],
                      'matches_prior': report['s8_2_flag_count_matches'],
                      'unresolved_calendar_rows': report['2019_20_unresolved_calendar_rows']}, indent=2))


if __name__ == '__main__':
    main()
