"""S8.22.7.10: offline, fail-closed retrospective date schedule governance."""
import argparse
import csv
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

DATE = '2023-11-15'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def within(root, path):
    p = Path(path)
    p = (p if p.is_absolute() else root / p).resolve()
    if not p.is_relative_to(root.resolve()):
        raise ValueError('Path escapes project root')
    if not p.is_file():
        raise ValueError(f'Missing file: {p}')
    return p

def read_json(root, path):
    return json.loads(within(root, path).read_text(encoding='utf-8'))

def read_csv(root, path):
    with within(root, path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def time_utc(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Naive tipoff timestamp')
    return dt.astimezone(timezone.utc)

def audit(root, official_receipt, official_report, provider_csv, provider_capture_report,
          directory_review, verified_crosswalk, comparison_report, directory_receipt=None):
    root = Path(root).resolve()
    checks = {}
    issues = []
    def check(name, ok, detail=''):
        checks[name] = {'status': 'PASS' if ok else 'BLOCKED', 'detail': detail}
        if not ok:
            issues.append(name + (': ' + detail if detail else ''))

    receipt = read_json(root, official_receipt)
    official = read_json(root, official_report)
    capture = read_json(root, provider_capture_report)
    directory = read_json(root, directory_review)
    prior = read_json(root, comparison_report)
    provider_path = within(root, provider_csv)
    mappings = read_csv(root, verified_crosswalk)

    check('official_receipt_date_and_url', receipt.get('date') == DATE and
          receipt.get('source_url') == 'https://www.nba.com/games?date=2023-11-15')
    source_path = within(root, receipt['evidence_path'])
    check('official_source_sha256', sha(source_path) == receipt.get('sha256') and
          source_path.stat().st_size == receipt.get('bytes') and
          receipt.get('sha256') == official.get('source_sha256'))
    check('official_report_provenance', official.get('milestone') == 'S8.22.7.7' and
          official.get('date') == DATE and official.get('source_url') == receipt.get('source_url'))

    expected_provider_hash = capture.get('provider_csv_sha256')
    check('provider_csv_sha256', isinstance(expected_provider_hash, str) and
          sha(provider_path) == expected_provider_hash)
    check('provider_capture_provenance', capture.get('date') == DATE and
          capture.get('provider_rows') == 8)
    check('directory_review', directory.get('date') == DATE and
          directory.get('status') == 'DIRECTORY_CROSSWALK_VERIFIED_CANDIDATE_GAME_AGREEMENT' and
          directory.get('team_identity_verified_from_directory') is True and
          directory.get('verified_rows') == 16 and not directory.get('issues'))
    if directory_receipt:
        dr = read_json(root, directory_receipt)
        db = within(root, dr['evidence_path'])
        check('directory_original_source_sha256', sha(db) == dr.get('sha256') == directory.get('source_sha256') and
              db.stat().st_size == dr.get('bytes'))
    else:
        checks['directory_original_source_sha256'] = {'status':'REVIEW_REQUIRED', 'detail':'Directory receipt not provided; review report only'}

    check('prior_comparison_identity', prior.get('milestone') == 'S8.22.7.8' and
          prior.get('date') == DATE and prior.get('matched_games') == 8 and not prior.get('issues'))
    check('crosswalk_evidence_sha256', len(mappings) == 16 and all(
        r.get('evidence_sha256') == directory.get('source_sha256') and
        r.get('verification_status') == 'DIRECTORY_BYTES_MATCH' for r in mappings))
    ids = [r.get('provider_team_id') for r in mappings]
    abbrs = [r.get('nba_abbreviation') for r in mappings]
    check('crosswalk_one_to_one', len(set(ids)) == len(ids) == 16 and len(set(abbrs)) == 16)
    lookup = {r['provider_team_id']:r['nba_abbreviation'] for r in mappings}

    provider = read_csv(root, provider_csv)
    official_games = official.get('official_games', [])
    check('source_game_counts', len(provider) == len(official_games) == 8 and
          official.get('official_game_count') == 8)
    matches = []
    seen_provider = set()
    seen_official = set()
    official_index = {}
    for g in official_games:
        key = (g['home_team'], g['away_team'])
        if key in official_index: issues.append('duplicate_official_matchup')
        official_index[key] = g
        if g['official_nba_game_id'] in seen_official: issues.append('duplicate_official_game_id')
        seen_official.add(g['official_nba_game_id'])
    for row in provider:
        pid = row.get('provider_game_id')
        if pid in seen_provider: issues.append('duplicate_provider_game_id')
        seen_provider.add(pid)
        if row.get('game_date') != DATE: issues.append('provider_game_date_mismatch:' + str(pid))
        home = lookup.get(row.get('home_provider_team_id'))
        away = lookup.get(row.get('away_provider_team_id'))
        if not home or not away:
            issues.append('unmapped_team:' + str(pid))
            continue
        official_game = official_index.get((home, away))
        if not official_game:
            issues.append('missing_official_matchup:' + str(pid))
            continue
        delta = abs((time_utc(row['tipoff_utc']) - time_utc(official_game['tipoff_utc'])).total_seconds())
        if delta != 0: issues.append('tipoff_disagreement:' + str(pid))
        matches.append({'provider_game_id':pid,'official_nba_game_id':official_game['official_nba_game_id'],
                        'home_team':home,'away_team':away,'tipoff_delta_seconds':delta})
    check('reconstructed_game_agreement', len(matches) == 8 and not any(
        i.startswith(('duplicate_', 'unmapped_', 'missing_official_', 'tipoff_', 'provider_game_date_')) for i in issues))
    prior_pairs = {(str(m['provider_game_id']),str(m['official_nba_game_id'])) for m in prior.get('matches',[])}
    rebuilt_pairs = {(str(m['provider_game_id']),str(m['official_nba_game_id'])) for m in matches}
    check('reconstruction_agrees_with_prior', len(prior_pairs) == 8 and prior_pairs == rebuilt_pairs)
    game_agreement = 'PASS' if not issues else 'BLOCKED'
    # Retrospective page extraction and two agreeing sources do NOT certify exhaustive full-date coverage.
    completeness = 'REVIEW_REQUIRED' if game_agreement == 'PASS' else 'BLOCKED'
    checks['date_schedule_completeness'] = {
        'status':completeness,
        'detail':'No independently governed proof that the archived date-page listing is exhaustive for the entire date; count agreement is not completeness certification.'}
    checks['historical_asof'] = {'status':'BLOCKED','detail':'2026 retrieval does not prove availability before 2023 tipoffs.'}
    report = {'milestone':'S8.22.7.10','date':DATE,'mode':'OFFLINE_FAIL_CLOSED_SCHEDULE_GOVERNANCE',
              'official_source_sha256':receipt.get('sha256'),'provider_csv_sha256':sha(provider_path),
              'directory_source_sha256':directory.get('source_sha256'),
              'checks':checks,'issues':issues,'reconstructed_matches':matches,
              'game_agreement':game_agreement,'date_completeness':'NOT_CERTIFIED',
              'historical_asof':'NOT_CERTIFIED','routine_collection_approved':False,
              'training_eligible':False,'decision':'BLOCK_TRAINING',
              'next_evidence':'Independent, dated, authoritative evidence establishing complete official date slate and historical publication provenance.'}
    return report

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ('project-root','official-receipt','official-report','provider-csv','provider-capture-report',
                'directory-review','verified-crosswalk','comparison-report'):
        p.add_argument('--'+arg, required=True)
    p.add_argument('--directory-receipt')
    args = vars(p.parse_args())
    root = Path(args.pop('project_root')).resolve()
    try:
        report = audit(root, **{k.replace('-','_'):v for k,v in args.items()})
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        p.exit(2, f'BLOCKED: {type(exc).__name__}: {exc}\n')
    dest = root/'research/p0_s8/s8_22_7_10/results'/DATE
    dest.mkdir(parents=True,exist_ok=True)
    path = dest/f'schedule_governance_{uuid.uuid4().hex}.json'
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',path)
    print('GAME AGREEMENT:',report['game_agreement'])
    print('DATE COMPLETENESS:',report['date_completeness'])
    print('ISSUES:',len(report['issues']))
    print('DECISION:',report['decision'])
    if report['issues']:
        p.exit(1,'Evidence conflict: review report before proceeding.\n')

if __name__ == '__main__':
    main()
