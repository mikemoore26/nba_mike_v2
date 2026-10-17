"""S8.22.10.16: offline, date-aware classification of out-of-slate team notices.

No fabricated dates, game IDs, source authentication, or injury certifications.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

DATE = '2023-11-15'
EXPECTED_IDS = {'T-007', 'T-008', 'T-009', 'T-010'}
EXPECTED_MATCHUPS = {'BKN@MIA': {'BKN', 'MIA'}, 'OKC@GSW': {'OKC', 'GSW'}}
FIELDS = ['record_id','record_type','source_game_date_candidate','source_matchup_candidate','source_team_candidate','source_page','source_pdf_context','classification','reason','verified_game_id','proposed_corrected_date','source_date_verified','player_status_certified','historical_asof','training_eligible']

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_csv(path):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames: raise ValueError('Missing CSV header')
        return list(reader)

def discover(root):
    candidates = sorted((root/f'research/p0_s8/s8_22_10_15/results/{DATE}').glob('*/review.json'))
    candidates = [p for p in candidates if json.loads(p.read_text(encoding='utf-8')).get('milestone') == 'S8.22.10.15']
    if len(candidates) != 1: raise ValueError(f'Expected one S8.22.10.15 report; found {len(candidates)}. Use --report.')
    return candidates[0]

def classify(row):
    rid = row['record_id'].strip()
    kind = row['record_type'].strip().upper()
    matchup = row['matchup_candidate'].strip().upper()
    team = row['team_candidate'].strip().upper()
    date = row['game_date_candidate'].strip()
    if rid not in EXPECTED_IDS: raise ValueError('Unexpected exception record ID: ' + rid)
    if kind != 'TEAM_SUBMISSION': raise ValueError(f'{rid}: expected team-submission notice, not player status')
    if matchup not in EXPECTED_MATCHUPS or team not in EXPECTED_MATCHUPS[matchup]:
        raise ValueError(f'{rid}: team/matchup conflict; cannot classify automatically')
    if not row['source_pdf_context'].strip() or not row['source_page'].strip().isdigit():
        raise ValueError(f'{rid}: missing PDF provenance')
    # A candidate date from an extracted PDF is not independently verified.
    if date == DATE:
        classification = 'OUT_OF_VERIFIED_SLATE_REVIEW_REQUIRED'
        reason = 'MATCHUP_NOT_IN_EIGHT_GAME_VERIFIED_SLATE'
    else:
        classification = 'DATE_SCOPE_MISMATCH_REVIEW_REQUIRED'
        reason = 'EXTRACTED_DATE_DIFFERS_FROM_TARGET_AND_MATCHUP_OFF_SLATE'
    return {'record_id':rid, 'record_type':kind,'source_game_date_candidate':date,
            'source_matchup_candidate':matchup,'source_team_candidate':team,
            'source_page':row['source_page'],'source_pdf_context':row['source_pdf_context'],
            'classification':classification,'reason':reason,'verified_game_id':'',
            'proposed_corrected_date':'','source_date_verified':'NO',
            'player_status_certified':'NO','historical_asof':'NOT_CERTIFIED','training_eligible':'NO'}

def run(root, report_path=None):
    root = Path(root).resolve()
    report_path = Path(report_path).resolve() if report_path else discover(root)
    if not report_path.is_relative_to(root): raise ValueError('Report must be inside project')
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if report.get('milestone') != 'S8.22.10.15' or report.get('mapping_exceptions_analyzed') != 4 or report.get('training_decision') != 'BLOCK_TRAINING':
        raise ValueError('Upstream report invalid')
    if report.get('reason_counts') != {'DATE_MISMATCH_NO_AUTOMATIC_REPAIR':4}:
        raise ValueError('Upstream reason counts changed; investigate')
    prior = report_path.parent/'mapping_exception_analysis.csv'
    if not prior.is_file(): raise FileNotFoundError('Missing upstream exception analysis')
    rows = read_csv(prior)
    if len(rows) != 4 or {r['record_id'] for r in rows} != EXPECTED_IDS:
        raise ValueError('Expected exactly four distinct original exception IDs')
    if any(r['mapping_resolution'] != 'MANUAL_EXCEPTION_REQUIRED' or r['reason'] != 'DATE_MISMATCH_NO_AUTOMATIC_REPAIR' for r in rows):
        raise ValueError('Upstream exceptions changed')
    classified = [classify(row) for row in sorted(rows, key=lambda r:r['record_id'])]
    # Source CSV and upstream report both enter the output fingerprint.
    token = hashlib.sha256((digest(prior)+digest(report_path)).encode()).hexdigest()[:16]
    out = root/f'research/p0_s8/s8_22_10_16/results/{DATE}/{token}'
    out.mkdir(parents=True, exist_ok=True)
    with (out/'team_notice_date_scope.csv').open('w',newline='',encoding='utf-8') as stream:
        writer = csv.DictWriter(stream,fieldnames=FIELDS)
        writer.writeheader(); writer.writerows(classified)
    summary = {'milestone':'S8.22.10.16','game_date':DATE,'source_report':str(report_path),
               'source_report_sha256':digest(report_path),'source_analysis_sha256':digest(prior),
               'records_classified':len(classified), 'classification_counts':dict(Counter(r['classification'] for r in classified)),
               'team_submission_notices':4,'player_injury_records_reclassified':0,
               'corrected_dates_asserted':0,'verified_game_ids_added':0,'injury_rows_certified':0,
               'historical_asof':'NOT_CERTIFIED','player_identity':'NOT_CERTIFIED',
               'research_status':'RESEARCH_ONLY','training_decision':'BLOCK_TRAINING',
               'next_action':'Verify source PDF publication and game dates independently before any date correction. Continue 44 player candidate identity and as-of evidence audit separately.',
               'note':'Out-of-slate classification is not proof of a different game date. No source ledger or upstream evidence modified.'}
    (out/'review.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',out/'review.json');print(json.dumps(summary,indent=2))
    for row in classified: print(f"{row['record_id']} {row['source_matchup_candidate']} {row['source_team_candidate']}: {row['classification']}")
    return summary

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',default='.')
    parser.add_argument('--report',help='Explicit S8.22.10.15 review.json inside project')
    args = parser.parse_args()
    try: run(args.project_root,args.report)
    except (ValueError,KeyError,OSError) as exc: parser.exit(2,'FAIL CLOSED: '+str(exc)+'\n')

if __name__ == '__main__': main()
