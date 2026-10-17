"""S8.22.10.13: deterministic, fail-closed AUTOMATED game-ID evidence verification.

Automated verification is NOT independent human certification or training approval.
"""
import argparse
from collections import Counter
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path

DATE = '2023-11-15'
EXPECTED_CROSSWALK_SHA256 = 'ca59d35f24e2ac8c1ba70971b5fec60ec7ce654a938b4d9d1902848f8d115212'
FIELDS = ['game_date','away_at_home','nba_game_id','verification_status','schedule_integrity','page_integrity','consistency','schedule_sha256','game_page_sha256','crosswalk_sha256','schedule_reconciliation_sha256','page_evidence_sha256']

def load_auditor(root):
    script = root / 'research/p0_s8/s8_22_10_12/run_s8_22_10_12.py'
    if not script.is_file():
        raise FileNotFoundError('Required S8.22.10.12 auditor missing: ' + str(script))
    spec = importlib.util.spec_from_file_location('s8221012_for_s8221013', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def verified_crosswalk(root, expected_sha=EXPECTED_CROSSWALK_SHA256):
    base = root / f'research/p0_s8/s8_22_10_7/results/{DATE}'
    candidates = sorted(base.glob('*/provisional_game_id_crosswalk.csv'))
    matches = [p for p in candidates if hashlib.sha256(p.read_bytes()).hexdigest() == expected_sha]
    if len(matches) != 1:
        raise ValueError(f'Expected one exact-SHA256 crosswalk; found {len(matches)} matches among {len(candidates)} candidates. No fallback permitted.')
    return matches[0]

def verify(root, crosswalk=None, schedule_csv=None, page_csv=None, expected_sha=EXPECTED_CROSSWALK_SHA256):
    root = root.resolve()
    auditor = load_auditor(root)
    base = root / 'research/p0_s8'
    cw = Path(crosswalk).resolve() if crosswalk else verified_crosswalk(root, expected_sha)
    if not cw.is_file() or hashlib.sha256(cw.read_bytes()).hexdigest() != expected_sha:
        raise ValueError('Crosswalk SHA256 mismatch; fail closed')
    token = expected_sha[:16]
    sc = Path(schedule_csv).resolve() if schedule_csv else base / f's8_22_10_11/results/{DATE}/{token}/independent_schedule_reconciliation.csv'
    pg = Path(page_csv).resolve() if page_csv else base / f's8_22_10_10/results/{DATE}/{token}/game_page_evidence.csv'
    archive = base / f's8_22_10_11/evidence/{DATE}'
    rows, _, human_certified = auditor.audit(root, cw, sc, pg,
        archive / f'nba_schedule_{DATE}.html', archive / f'nba_schedule_{DATE}.receipt.json',
        base / f's8_22_10_10/evidence/{DATE}', None)
    if human_certified:
        raise AssertionError('Automatic audit unexpectedly returned human-certified rows')
    verified = []
    for r in rows:
        status = ('AUTOMATED_VERIFIED' if r['schedule_integrity'] == 'INTEGRITY_PASS'
                  and r['page_integrity'] == 'INTEGRITY_PASS' and r['consistency'] == 'PASS'
                  else 'MANUAL_EXCEPTION_REQUIRED')
        verified.append(dict(game_date=r['game_date'], away_at_home=r['away_at_home'],
            nba_game_id=r['discovered_nba_game_id'], verification_status=status,
            schedule_integrity=r['schedule_integrity'], page_integrity=r['page_integrity'],
            consistency=r['consistency'], schedule_sha256=auditor.sha((archive/f'nba_schedule_{DATE}.html').read_bytes()) if (archive/f'nba_schedule_{DATE}.html').exists() else '',
            game_page_sha256=next((x.get('snapshot_sha256','') for x in auditor.csv_rows(pg) if x.get('away_at_home')==r['away_at_home']),''),
            crosswalk_sha256=expected_sha,
            schedule_reconciliation_sha256=auditor.sha(sc.read_bytes()),
            page_evidence_sha256=auditor.sha(pg.read_bytes())))
    return verified, {'crosswalk':cw,'schedule_csv':sc,'page_csv':pg}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',default='.')
    p.add_argument('--crosswalk')
    p.add_argument('--schedule-reconciliation')
    p.add_argument('--page-evidence')
    args=p.parse_args()
    root=Path(args.project_root).resolve()
    rows, sources=verify(root,args.crosswalk,args.schedule_reconciliation,args.page_evidence)
    counts=dict(Counter(r['verification_status'] for r in rows))
    base=root / f'research/p0_s8/s8_22_10_13/results/{DATE}'
    # Content-addressed outputs: distinct evidence versions never silently replace another version.
    evidence_hash=hashlib.sha256((''.join(hashlib.sha256(sources[k].read_bytes()).hexdigest() for k in ('crosswalk','schedule_csv','page_csv'))).encode()).hexdigest()[:16]
    out=base/evidence_hash
    out.mkdir(parents=True,exist_ok=True)
    auditor=load_auditor(root)
    auditor.write_csv(out/'automated_game_id_verification.csv',FIELDS,rows)
    exceptions=[r for r in rows if r['verification_status'] != 'AUTOMATED_VERIFIED']
    auditor.write_csv(out/'manual_exception_queue.csv',FIELDS,exceptions)
    report={'milestone':'S8.22.10.13','game_date':DATE,'target_games':len(rows),
        'status_counts':counts,'automated_verified':counts.get('AUTOMATED_VERIFIED',0),
        'manual_exceptions':len(exceptions),'human_certified':0,
        'crosswalk_source':str(sources['crosswalk']),
        'crosswalk_sha256':EXPECTED_CROSSWALK_SHA256,
        'independent_human_review':'NOT_PERFORMED',
        'historical_asof':'NOT_CERTIFIED','player_identity':'NOT_CERTIFIED',
        'injury_report_reviews_completed':0,'research_status':'RESEARCH_ONLY',
        'training_decision':'BLOCK_TRAINING',
        'note':'AUTOMATED_VERIFIED means archived evidence passes local integrity and identity consistency checks. Local capture receipts do not authenticate the publisher or establish historical as-of availability. No human approvals are fabricated.'}
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',out/'review.json')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
