"""S8.22.10.14: offline, fail-closed injury-ledger triage. No player/as-of certification."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re

DATE = '2023-11-15'
EXPECTED_CROSSWALK_SHA = 'ca59d35f24e2ac8c1ba70971b5fec60ec7ce654a938b4d9d1902848f8d115212'
EXPECTED_GAME_IDS = {'DAL@WAS':'0022300192','NYK@ATL':'0022300193','BOS@PHI':'0022300194','MIL@TOR':'0022300195','ORL@CHI':'0022300196','MIN@PHX':'0022300197','SAC@LAL':'0022300198','CLE@POR':'0022300199'}
VALID_STATUSES = {'OUT','QUESTIONABLE','DOUBTFUL','PROBABLE','AVAILABLE'}
OUTPUT_FIELDS = ['record_id','record_type','game_date_candidate','matchup_candidate','nba_game_id','team_candidate','name_or_notice_candidate','status_candidate','reason_candidate','source_page','source_y','source_pdf_context','triage_status','triage_reasons','game_id_evidence','player_identity','injury_status_evidence','historical_asof','training_eligible']

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def read_csv(path):
    with path.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames: raise ValueError(f'CSV has no header: {path}')
        return list(reader)

def discover_ledger(root):
    base=root/f'research/p0_s8/s8_22_10_7/results/{DATE}'
    candidates=sorted(base.glob('*/player_and_team_manual_review.csv'))
    # Resolve through original verified crosswalk, not a guessed output folder.
    eligible=[p for p in candidates if (p.parent/'provisional_game_id_crosswalk.csv').is_file() and sha(p.parent/'provisional_game_id_crosswalk.csv')==EXPECTED_CROSSWALK_SHA]
    if len(eligible)!=1: raise ValueError(f'Expected exactly one ledger paired with verified crosswalk; found {len(eligible)}. Supply --ledger.')
    return eligible[0]

def discover_game_report(root):
    base=root/f'research/p0_s8/s8_22_10_13/results/{DATE}'
    reports=sorted(base.glob('*/review.json'))
    valid=[]
    for p in reports:
        try:
            obj=json.loads(p.read_text(encoding='utf-8'))
            if obj.get('milestone')=='S8.22.10.13' and obj.get('crosswalk_sha256')==EXPECTED_CROSSWALK_SHA and obj.get('automated_verified')==8 and obj.get('manual_exceptions')==0 and obj.get('training_decision')=='BLOCK_TRAINING': valid.append(p)
        except (ValueError, OSError): pass
    if len(valid)!=1: raise ValueError(f'Expected exactly one verified S8.22.10.13 report; found {len(valid)}. Supply --game-report.')
    return valid[0]

def validate_game_report(path):
    report=json.loads(path.read_text(encoding='utf-8'))
    required={'milestone':'S8.22.10.13','crosswalk_sha256':EXPECTED_CROSSWALK_SHA,'automated_verified':8,'manual_exceptions':0,'training_decision':'BLOCK_TRAINING'}
    if any(report.get(k)!=v for k,v in required.items()): raise ValueError('Game-ID report fails provenance/governance checks')
    csv_path=path.parent/'automated_game_id_verification.csv'
    # Check report's actual CSV if available; fail closed if not.
    if not csv_path.is_file():
        matches=sorted(path.parent.glob('*.csv'))
        raise ValueError(f'Expected automated_game_id_verification.csv; found {[p.name for p in matches]}. Inspect S8.22.10.13 output.')
    rows=read_csv(csv_path)
    if len(rows)!=8 or len({r.get('away_at_home') for r in rows})!=8: raise ValueError('Game-ID CSV count or uniqueness mismatch')
    for r in rows:
        if r.get('game_date')!=DATE or r.get('verification_status')!='AUTOMATED_VERIFIED' or EXPECTED_GAME_IDS.get(r.get('away_at_home'))!=r.get('nba_game_id'):
            raise ValueError('Game-ID CSV not fully verified or inconsistent')
    return {r['away_at_home']:r['nba_game_id'] for r in rows},csv_path

def triage(rows, games):
    required={'record_id','record_type','game_date_candidate','matchup_candidate','team_candidate','name_or_notice_candidate','status_candidate','reason_candidate','page','y','pdf_context_excerpt','parser_header_artifact_flag'}
    if not rows or not required.issubset(rows[0]): raise ValueError('Missing injury ledger rows/fields: '+str(sorted(required-set(rows[0]) if rows else required)))
    ids=[r.get('record_id','') for r in rows]
    if any(not i for i in ids) or len(set(ids))!=len(ids): raise ValueError('Missing or duplicate record IDs')
    out=[]
    for r in rows:
        reasons=[]
        matchup=r['matchup_candidate'].strip(); kind=r['record_type'].strip().upper(); team=r['team_candidate'].strip().upper()
        if r['game_date_candidate']!=DATE or matchup not in games: reasons.append('GAME_MAPPING_UNVERIFIED')
        if kind not in ('PLAYER','TEAM_SUBMISSION'): reasons.append('UNKNOWN_RECORD_TYPE')
        if r['parser_header_artifact_flag'].strip().upper()=='YES': reasons.append('PARSER_HEADER_ARTIFACT')
        if not re.fullmatch(r'\d+',r['page'].strip()) or int(r['page'])<1: reasons.append('INVALID_PDF_PAGE')
        if not r['pdf_context_excerpt'].strip(): reasons.append('MISSING_SOURCE_EXCERPT')
        if matchup in games:
            a,h=matchup.split('@');
            if team not in (a,h): reasons.append('TEAM_REQUIRES_REVIEW')
        if kind=='PLAYER':
            if not r['name_or_notice_candidate'].strip(): reasons.append('MISSING_PLAYER_NAME')
            if r['status_candidate'].strip().upper() not in VALID_STATUSES: reasons.append('STATUS_REQUIRES_REVIEW')
            reasons.append('PLAYER_IDENTITY_NOT_CERTIFIED')
        elif kind=='TEAM_SUBMISSION': reasons.append('TEAM_SUBMISSION_NOT_PLAYER_STATUS')
        reasons.append('HISTORICAL_ASOF_NOT_CERTIFIED')
        # A PDF parser candidate is never automatically promoted to verified injury fact.
        out.append({'record_id':r['record_id'],'record_type':kind,'game_date_candidate':r['game_date_candidate'],'matchup_candidate':matchup,'nba_game_id':games.get(matchup,'') if r['game_date_candidate']==DATE else '',
          'team_candidate':r['team_candidate'],'name_or_notice_candidate':r['name_or_notice_candidate'],'status_candidate':r['status_candidate'],'reason_candidate':r['reason_candidate'],
          'source_page':r['page'],'source_y':r['y'],'source_pdf_context':r['pdf_context_excerpt'],
          'triage_status':'EXCEPTION_REVIEW_REQUIRED' if any(x not in ('PLAYER_IDENTITY_NOT_CERTIFIED','HISTORICAL_ASOF_NOT_CERTIFIED','TEAM_SUBMISSION_NOT_PLAYER_STATUS') for x in reasons) else 'EVIDENCE_PENDING',
          'triage_reasons':'|'.join(reasons),'game_id_evidence':'AUTOMATED_VERIFIED' if matchup in games and r['game_date_candidate']==DATE else 'UNVERIFIED',
          'player_identity':'NOT_CERTIFIED','injury_status_evidence':'NOT_CERTIFIED','historical_asof':'NOT_CERTIFIED','training_eligible':'NO'})
    return out

def write_csv(path, rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=OUTPUT_FIELDS);writer.writeheader();writer.writerows(rows)

def run(root, ledger=None, game_report=None):
    root=root.resolve()
    ledger=Path(ledger).resolve() if ledger else discover_ledger(root)
    game_report=Path(game_report).resolve() if game_report else discover_game_report(root)
    if not ledger.is_file() or not game_report.is_file(): raise FileNotFoundError('Ledger or game report missing')
    if not ledger.is_relative_to(root) or not game_report.is_relative_to(root): raise ValueError('Inputs must be inside project')
    games,game_csv=validate_game_report(game_report)
    rows=read_csv(ledger)
    if len(rows)!=54: raise ValueError(f'Expected 54 original review records; found {len(rows)}. Fail closed.')
    processed=triage(rows,games)
    source_sha=sha(ledger); game_sha=sha(game_csv)
    token=hashlib.sha256((source_sha+game_sha).encode()).hexdigest()[:16]
    output=root/f'research/p0_s8/s8_22_10_14/results/{DATE}/{token}'
    output.mkdir(parents=True,exist_ok=True)
    write_csv(output/'injury_evidence_triage.csv',processed)
    write_csv(output/'exception_queue.csv',[r for r in processed if r['triage_status']=='EXCEPTION_REVIEW_REQUIRED'])
    report={'milestone':'S8.22.10.14','game_date':DATE,'source_ledger':str(ledger),'source_ledger_sha256':source_sha,'game_id_report':str(game_report),'game_id_report_sha256':sha(game_report),'game_id_csv_sha256':game_sha,'records_total':len(processed),'record_type_counts':dict(Counter(r['record_type'] for r in processed)),'triage_counts':dict(Counter(r['triage_status'] for r in processed)),'reason_counts':dict(Counter(reason for r in processed for reason in r['triage_reasons'].split('|'))),'game_ids_automated_verified':sum(r['game_id_evidence']=='AUTOMATED_VERIFIED' for r in processed),'injury_rows_certified':0,'player_identity':'NOT_CERTIFIED','injury_status_evidence':'NOT_CERTIFIED','historical_asof':'NOT_CERTIFIED','research_status':'RESEARCH_ONLY','training_decision':'BLOCK_TRAINING','warning':'Triage is not player/status or historical publication-time verification; raw PDF candidates cannot be promoted automatically.'}
    (output/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',output/'review.json');print(json.dumps(report,indent=2));return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project-root',default='.');p.add_argument('--ledger');p.add_argument('--game-report');a=p.parse_args()
    try: run(Path(a.project_root),a.ledger,a.game_report)
    except (ValueError,FileNotFoundError,KeyError) as exc: p.exit(2,'FAIL CLOSED: '+str(exc)+'\n')
if __name__=='__main__':main()
