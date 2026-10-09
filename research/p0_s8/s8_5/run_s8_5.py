"""S8.5: offline, read-only historical feature feasibility / leakage audit.

This milestone builds no model. All game-day outcome values are excluded from
same-game feature eligibility; only prior-game rows are used for demonstrations.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

SEASONS = ('2019-20', '2023-24', '2025-26')
COLUMNS = ('game_id', 'event_date', 'player_id', 'team_id', 'min', 'pts', 'reb', 'ast', 'fg3m')
TARGETS = ('min', 'pts', 'reb', 'ast', 'fg3m')


def number(raw):
    try:
        n = float(raw)
        if not (-1e9 < n < 1e9):
            return None
        return n
    except (TypeError, ValueError):
        return None


def inspect(path: Path, season: str):
    result = {'season': season, 'path': str(path), 'exists': path.is_file(),
              'rows': 0, 'eligible_prior_history_rows': 0, 'same_day_ambiguous_rows': 0,
              'duplicate_player_game_rows': 0, 'invalid_date_rows': 0,
              'invalid_target_values': 0, 'missing_columns': [], 'date_conflict_games': 0,
              'status': 'BLOCKED'}
    if not path.is_file():
        result['reason'] = 'MISSING_SNAPSHOT'
        return result
    result['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(encoding='utf-8-sig', newline='') as fh:
        reader = csv.DictReader(fh)
        cols = set(reader.fieldnames or [])
        result['missing_columns'] = sorted(set(COLUMNS) - cols)
        if result['missing_columns']:
            result['reason'] = 'MISSING_REQUIRED_COLUMNS'
            return result
        records = []
        game_dates = defaultdict(set)
        keys = set()
        for row in reader:
            result['rows'] += 1
            key = (row['player_id'], row['game_id'])
            if key in keys:
                result['duplicate_player_game_rows'] += 1
            keys.add(key)
            try:
                d = date.fromisoformat(row['event_date'][:10])
            except (TypeError, ValueError):
                result['invalid_date_rows'] += 1
                continue
            game_dates[row['game_id']].add(d.isoformat())
            values = {t: number(row[t]) for t in TARGETS}
            result['invalid_target_values'] += sum(v is None or v < 0 for v in values.values())
            records.append((row['player_id'], d, row['game_id'], values))
    result['date_conflict_games'] = sum(len(ds) > 1 for ds in game_dates.values())
    # Strictly earlier dates only: same-day games are not assumed to be ordered.
    by_player = defaultdict(list)
    for player, d, game, vals in records:
        by_player[player].append((d, game, vals))
    examples = []
    for player, rows in by_player.items():
        rows.sort(key=lambda x: (x[0], x[1]))
        earlier = 0
        for idx, (d, game, vals) in enumerate(rows):
            if idx and rows[idx - 1][0] == d:
                result['same_day_ambiguous_rows'] += 1
            if idx and rows[idx - 1][0] < d:
                earlier = idx
            if earlier > 0:
                result['eligible_prior_history_rows'] += 1
                if len(examples) < 3:
                    prior = rows[:earlier]
                    examples.append({'player_id': player, 'game_id': game,
                                     'event_date': d.isoformat(), 'prior_game_count': len(prior),
                                     'last_prior_date': prior[-1][0].isoformat(),
                                     'prior_min_mean': round(sum(x[2]['min'] for x in prior if x[2]['min'] is not None) / len(prior), 4) if all(x[2]['min'] is not None for x in prior) else None})
    result['examples'] = examples
    result['status'] = 'CANDIDATE_ONLY_ASOF_NOT_CERTIFIED' if not any((result['duplicate_player_game_rows'], result['invalid_date_rows'], result['invalid_target_values'], result['date_conflict_games'])) else 'NEEDS_REPAIR'
    result['reason'] = 'PRIOR_GAME_ORDER_PLAUSIBLE_BUT_PUBLICATION_AND_FEATURE_LINEAGE_UNVERIFIED'
    return result


def run(root: Path):
    rows = [inspect(root / 'research' / 'p0_s4' / 's5_1' / 'snapshots' / f'player_gamelogs_{s}.csv', s) for s in SEASONS]
    output = root / 'research' / 'p0_s8' / 's8_5' / 'results'
    output.mkdir(parents=True, exist_ok=True)
    report = {'milestone': 'S8.5', 'mode': 'OFFLINE_FEATURE_LINEAGE_FEASIBILITY',
              'status': 'RESEARCH_ONLY', 'decision': 'BLOCK_TRAINING',
              'historical_roster_transaction_features': 'BLOCKED_S7_51',
              'calendar_gate': 'S8_4_OFFICIAL_SOURCE_TIMEOUT_88_UNVERIFIED',
              'calendar_research_decision': 'PAUSE_ENDPOINT_RETRIES',
              'dataset_count': len(rows), 'total_rows': sum(r['rows'] for r in rows),
              'candidate_prior_history_rows': sum(r['eligible_prior_history_rows'] for r in rows),
              'dataset_status_counts': dict(Counter(r['status'] for r in rows)),
              'datasets': rows, 'feature_policy': {
                  'allowed_for_offline_demonstration': ['strictly_prior_date_player_min_mean', 'strictly_prior_date_player_pts_mean', 'strictly_prior_date_player_reb_mean', 'strictly_prior_date_player_ast_mean', 'strictly_prior_date_player_fg3m_mean'],
                  'not_approved_for_training': ['all_features_until_lineage_and_asof_gate_pass'],
                  'forbidden_same_game_inputs': list(TARGETS) + ['team_id', 'game_id_as_predictor'],
                  'historical_roster_injury_market': 'BLOCKED_UNVERIFIED'},
              'limitations': ['A past event date is not proof of publication or feature availability before a later tipoff.',
                              'Player game-log presence is a postgame participant universe; no historical pregame player universe established.',
                              'No DNP or missing-game reconciliation, no historical roster or injury eligibility.',
                              'Calendar verification is still unresolved for 88 restart games.',
                              'No models trained, evaluated, or approved for betting.']}
    (output / 's8_5_report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    with (output / 's8_5_dataset_review.csv').open('w', newline='', encoding='utf-8') as fh:
        fields = ['season', 'status', 'rows', 'eligible_prior_history_rows', 'same_day_ambiguous_rows', 'duplicate_player_game_rows', 'invalid_date_rows', 'invalid_target_values', 'date_conflict_games', 'sha256', 'reason']
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction='ignore')
        writer.writeheader(); writer.writerows(rows)
    print(f"S8.5: {report['total_rows']} rows; {report['candidate_prior_history_rows']} prior-history candidates; BLOCK_TRAINING")
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', type=Path, default=Path('.'))
    args = parser.parse_args()
    run(args.project_root.resolve())
