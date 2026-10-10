"""Offline, fail-closed team-directory evidence verification. No network access."""
import argparse
import csv
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

EXPECTED_DATE = '2023-11-15'
REQUIRED = {'provider_team_id','nba_abbreviation','verification_status','evidence_url','evidence_sha256','reviewed_by'}

def digest(data): return hashlib.sha256(data).hexdigest()

def fail(message): raise ValueError(message)

def safe_path(root, p):
    path = Path(p)
    path = (path if path.is_absolute() else root / path).resolve()
    if not path.is_relative_to(root.resolve()): fail('Evidence path escapes project root')
    return path

def verify_receipt(root, receipt_path):
    rp = safe_path(root, receipt_path)
    receipt = json.loads(rp.read_text(encoding='utf-8'))
    url = receipt.get('source_url','')
    u = urlparse(url)
    if u.scheme != 'https' or u.hostname != 'api.balldontlie.io' or u.path.rstrip('/') != '/v1/teams':
        fail('Receipt must identify official BALLDONTLIE /v1/teams endpoint')
    if u.username or u.password or u.fragment: fail('Unsafe URL')
    raw_path = safe_path(root, receipt['evidence_path'])
    if not raw_path.is_file(): fail('Archived source.bin missing')
    raw = raw_path.read_bytes()
    if len(raw) != int(receipt['bytes']) or digest(raw) != receipt['sha256']:
        fail('Archived source integrity mismatch')
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get('data'), list): fail('Expected directory JSON object with data list')
    teams = {}
    for team in data['data']:
        if not isinstance(team,dict): fail('Invalid team entry')
        tid = str(team.get('id',''))
        abbr = str(team.get('abbreviation','')).strip().upper()
        if not tid.isdecimal() or not abbr or tid in teams: fail('Invalid or duplicate team ID')
        teams[tid] = abbr
    if data.get('meta') and data['meta'].get('next_cursor') is not None:
        fail('Directory pagination detected: single capture is not complete')
    return receipt, teams

def run(root, receipt_path, crosswalk_path, comparison_path):
    root = Path(root).resolve()
    receipt, directory = verify_receipt(root, receipt_path)
    with safe_path(root, crosswalk_path).open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames): fail('Crosswalk schema mismatch')
        rows = list(reader)
    if not rows: fail('Empty crosswalk')
    comparison = json.loads(safe_path(root, comparison_path).read_text(encoding='utf-8'))
    if comparison.get('milestone') != 'S8.22.7.8' or comparison.get('date') != EXPECTED_DATE:
        fail('Wrong comparison report')
    if comparison.get('issues') or comparison.get('matched_games') != 8 or len(comparison.get('matches',[])) != 8:
        fail('Prior comparison is not clean 8/8')
    seen=set(); issues=[]; verified=[]
    for row in rows:
        tid = row['provider_team_id'].strip()
        abbr = row['nba_abbreviation'].strip().upper()
        if tid in seen: issues.append(f'DUPLICATE_ID:{tid}'); continue
        seen.add(tid)
        if not tid.isdecimal(): issues.append(f'INVALID_ID:{tid}'); continue
        actual = directory.get(tid)
        if actual is None: issues.append(f'NOT_IN_DIRECTORY:{tid}')
        elif actual != abbr: issues.append(f'ABBREVIATION_CONFLICT:{tid}:{abbr}:{actual}')
        else: verified.append({'provider_team_id':tid,'nba_abbreviation':actual,'evidence_sha256':receipt['sha256'],'source_url':receipt['source_url'],'verification_status':'DIRECTORY_BYTES_MATCH'})
    # The comparison's team abbreviations must all be supported by distinct verified directory IDs.
    expected_abbrs = {m[k] for m in comparison['matches'] for k in ('home_team','away_team')}
    verified_abbrs = {r['nba_abbreviation'] for r in verified}
    missing = sorted(expected_abbrs - verified_abbrs)
    if missing: issues.append('MISSING_MATCHUP_ABBREVIATIONS:' + ','.join(missing))
    if len(verified) != len(expected_abbrs): issues.append('CROSSWALK_NOT_ONE_TO_ONE_FOR_MATCHUPS')
    # Reject unverified rows, not just missing matches, so bad data cannot slip through.
    status = 'DIRECTORY_CROSSWALK_VERIFIED_CANDIDATE_GAME_AGREEMENT' if not issues else 'DIRECTORY_CROSSWALK_CONFLICT'
    report = {'milestone':'S8.22.7.9','date':EXPECTED_DATE,'mode':'OFFLINE_DIRECTORY_BYTES_VERIFICATION',
      'source_url':receipt['source_url'],'source_sha256':receipt['sha256'],'source_retrieved_utc':receipt.get('retrieved_utc'),
      'crosswalk_rows':len(rows),'directory_rows':len(directory),'verified_rows':len(verified),
      'comparison_game_count':len(comparison['matches']),'issues':issues,'status':status,
      'team_identity_verified_from_directory':not issues,
      'provider_game_agreement':'CANDIDATE_ONLY_REQUIRES_REVIEW',
      'date_completeness':'NOT_CERTIFIED','historical_asof':'NOT_CERTIFIED',
      'routine_collection_approved':False,'training_eligible':False,'decision':'BLOCK_TRAINING',
      'limitations':['Directory response is retrieved retrospectively; historical as-of is not proven',
                     'Directory match does not certify schedule completeness',
                     'Game matchup comparison remains a candidate until separate evidence governance review']}
    output = root/'research/p0_s8/s8_22_7_9/results'/EXPECTED_DATE
    output.mkdir(parents=True,exist_ok=True)
    token = uuid.uuid4().hex
    (output/f'team_directory_review_{token}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    with (output/f'verified_team_crosswalk_{token}.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['provider_team_id','nba_abbreviation','evidence_sha256','source_url','verification_status'])
        writer.writeheader(); writer.writerows(verified)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',required=True)
    p.add_argument('--team-receipt',required=True)
    p.add_argument('--crosswalk-csv',required=True)
    p.add_argument('--comparison-report',required=True)
    args=p.parse_args()
    try:
        report=run(args.project_root,args.team_receipt,args.crosswalk_csv,args.comparison_report)
        print(f"DIRECTORY MATCHES: {report['verified_rows']}/{report['crosswalk_rows']}; ISSUES: {len(report['issues'])}")
        print('STATUS:',report['status']); print('DECISION:',report['decision'])
        if report['issues']: sys.exit(2)
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as e:
        print('FAIL_CLOSED:',e,file=sys.stderr); sys.exit(2)

if __name__=='__main__': main()
