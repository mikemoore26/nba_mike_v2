"""S8.22.10.7: non-destructive, fail-closed NBA game-ID and human-review preparation."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

# Existing research game IDs, carried as unverified historical hypotheses.
# IMPORTANT: no inference that their numeric ordering proves a matchup assignment.
PROVISIONAL = {
    ('2023-11-15', 'DAL@WAS'): '0022300192',
    ('2023-11-15', 'NYK@ATL'): '0022300193',
    ('2023-11-15', 'BOS@PHI'): '0022300194',
    ('2023-11-15', 'MIL@TOR'): '0022300195',
    ('2023-11-15', 'ORL@CHI'): '0022300196',
    ('2023-11-15', 'MIN@PHX'): '0022300197',
    ('2023-11-15', 'SAC@LAL'): '0022300198',
    ('2023-11-15', 'CLE@POR'): '0022300199',
}


def read_csv(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def reconcile(rows):
    if not rows:
        raise ValueError('Empty reconciliation input')
    required = {'game_date', 'pdf_matchup', 'external_status', 'record_count'}
    if not required.issubset(rows[0]):
        raise ValueError(f'Missing fields: {sorted(required-set(rows[0]))}')
    seen = set()
    out = []
    for r in rows:
        key = (r['game_date'], r['pdf_matchup'])
        if key in seen:
            raise ValueError(f'Duplicate game key: {key}')
        seen.add(key)
        if r['external_status'] != 'CORROBORATED_ORIENTATION':
            raise ValueError(f'Uncorroborated schedule entry: {key}')
        game_id = PROVISIONAL.get(key, '')
        out.append({
            'game_date': key[0], 'away_at_home': key[1],
            'provisional_nba_game_id': game_id,
            'game_id_status': 'UNVERIFIED_PROVISIONAL' if game_id else 'OUTSIDE_TARGET_SLATE',
            'game_id_evidence_url': '', 'game_id_evidence_description': '',
            'game_id_evidence_sha256': '', 'reviewer': '', 'reviewed_at_utc': '',
            'manual_game_id_decision': 'PENDING' if game_id else 'NOT_APPLICABLE',
            'record_count': r['record_count'],
            'source_orientation_status': r['external_status'],
        })
    target = set(PROVISIONAL)
    missing = target - seen
    if missing:
        raise ValueError(f'Target slate missing from schedule input: {sorted(missing)}')
    return out


def prepare_review(ledger, crosswalk):
    keys = {(r['game_date'], r['away_at_home']): r for r in crosswalk}
    ids = [r.get('record_id', '') for r in ledger]
    if not ledger or len(ids) != len(set(ids)) or any(not x for x in ids):
        raise ValueError('Empty ledger, missing IDs or duplicate IDs')
    required = {'record_id', 'game_date_candidate', 'matchup_candidate', 'manual_decision'}
    if not required.issubset(ledger[0]):
        raise ValueError(f'Missing ledger columns: {sorted(required-set(ledger[0]))}')
    out = []
    for row in ledger:
        key = (row['game_date_candidate'], row['matchup_candidate'])
        if key not in keys:
            raise ValueError(f'Ledger game missing from crosswalk: {key}')
        record = dict(row)
        record['provisional_nba_game_id'] = keys[key]['provisional_nba_game_id']
        record['game_id_status'] = keys[key]['game_id_status']
        record['s822107_manual_decision'] = 'PENDING'
        record['s822107_reviewer'] = ''
        record['s822107_reviewed_at_utc'] = ''
        record['s822107_evidence_reference'] = ''
        record['s822107_review_notes'] = ''
        record['s822107_training_eligible'] = 'NO'
        out.append(record)
    return out


def find_one(root, relative, filename):
    candidates = sorted((root / relative).glob('*/' + filename))
    if len(candidates) != 1:
        raise RuntimeError(f'Expected exactly one {filename} in {relative}; found {len(candidates)}. Supply an explicit path.')
    return candidates[0]


def run(root, schedule_path, ledger_path, output):
    schedule = read_csv(schedule_path)
    ledger = read_csv(ledger_path)
    crosswalk = reconcile(schedule)
    review_rows = prepare_review(ledger, crosswalk)
    if sum(int(x['record_count']) for x in crosswalk) != len(review_rows):
        raise ValueError('Schedule record counts do not equal ledger population')
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / 'provisional_game_id_crosswalk.csv', crosswalk, list(crosswalk[0]))
    write_csv(output / 'player_and_team_manual_review.csv', review_rows, list(review_rows[0]))
    report = {
        'milestone': 'S8.22.10.7',
        'schedule_sha256': hashlib.sha256(schedule_path.read_bytes()).hexdigest(),
        'ledger_sha256': hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
        'unique_games': len(crosswalk), 'provisional_game_ids': sum(bool(x['provisional_nba_game_id']) for x in crosswalk),
        'verified_game_ids': 0, 'manual_review_rows': len(review_rows), 'manual_reviews_completed': 0,
        'review_type_counts': dict(Counter(x.get('record_type', 'UNKNOWN') for x in review_rows)),
        'manual_review_status': 'ALL_PENDING', 'historical_asof': 'NOT_CERTIFIED',
        'player_identity': 'NOT_CERTIFIED', 'eligibility_and_dnp': 'NOT_CERTIFIED',
        'decision': 'BLOCK_TRAINING',
        'note': 'Provisional game IDs are inherited from prior research, not independently verified. Human review required.'
    }
    (output / 'review.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--project-root', default='.')
    p.add_argument('--schedule')
    p.add_argument('--ledger')
    p.add_argument('--output')
    args = p.parse_args()
    root = Path(args.project_root).resolve()
    schedule = Path(args.schedule).resolve() if args.schedule else find_one(root, 'research/p0_s8/s8_22_10_6/results/2023-11-15', 'unique_matchup_reconciliation.csv')
    ledger = Path(args.ledger).resolve() if args.ledger else find_one(root, 'research/p0_s8/s8_22_10_5/results/2023-11-15', 'manual_review_ledger.csv')
    token = hashlib.sha256(schedule.read_bytes() + ledger.read_bytes()).hexdigest()[:16]
    output = Path(args.output).resolve() if args.output else root / 'research/p0_s8/s8_22_10_7/results/2023-11-15' / token
    report = run(root, schedule, ledger, output)
    print('REPORT:', output / 'review.json')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
