"""Fail-closed, offline diagnosis of S8.22.10.14 mapping exceptions."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

DATE='2023-11-15'
GAMES={'DAL@WAS':'0022300192','NYK@ATL':'0022300193','BOS@PHI':'0022300194','MIL@TOR':'0022300195','ORL@CHI':'0022300196','MIN@PHX':'0022300197','SAC@LAL':'0022300198','CLE@POR':'0022300199'}
FIELDS=['record_id','record_type','game_date_candidate','matchup_candidate','team_candidate','original_nba_game_id','suggested_matchup','suggested_nba_game_id','mapping_resolution','reason','source_page','source_pdf_context','player_identity','injury_status_evidence','historical_asof','training_eligible']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def csv_read(path):
    with path.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames:raise ValueError('Missing CSV headers')
        return list(reader)
def locate(root):
    base=root/f'research/p0_s8/s8_22_10_14/results/{DATE}'
    found=[]
    for p in base.glob('*/review.json'):
        try:
            obj=json.loads(p.read_text(encoding='utf-8'))
            if obj.get('milestone')=='S8.22.10.14' and obj.get('records_total')==54 and obj.get('training_decision')=='BLOCK_TRAINING':found.append(p)
        except (OSError,ValueError):pass
    if len(found)!=1:raise ValueError(f'Expected exactly one valid S8.22.10.14 report, found {len(found)}; use --report')
    return found[0]

def classify(row):
    team=row['team_candidate'].strip().upper()
    matchup=row['matchup_candidate'].strip().upper()
    date=row['game_date_candidate'].strip()
    candidates=[m for m in GAMES if team in m.split('@')]
    proposed=candidates[0] if len(candidates)==1 else ''
    if date!=DATE:
        resolution,reason='MANUAL_EXCEPTION_REQUIRED','DATE_MISMATCH_NO_AUTOMATIC_REPAIR'
    elif matchup in GAMES and team not in matchup.split('@'):
        resolution,reason='MANUAL_EXCEPTION_REQUIRED','CONFLICTING_MATCHUP_AND_TEAM'
    elif matchup and matchup not in GAMES:
        resolution,reason='MANUAL_EXCEPTION_REQUIRED','UNRECOGNIZED_NONEMPTY_MATCHUP'
    elif not proposed:
        resolution,reason='MANUAL_EXCEPTION_REQUIRED','TEAM_NOT_UNIQUELY_MATCHED'
    elif matchup and matchup!=proposed:
        resolution,reason='MANUAL_EXCEPTION_REQUIRED','CONFLICTING_MATCHUP_AND_TEAM'
    else:
        resolution,reason='DETERMINISTIC_MAPPING_CANDIDATE','SAME_DATE_UNIQUE_TEAM_IN_VERIFIED_EIGHT_GAME_SLATE'
    # Never promote a source-extracted injury fact, even when game linkage is unambiguous.
    return {'record_id':row['record_id'],'record_type':row['record_type'],'game_date_candidate':date,'matchup_candidate':matchup,'team_candidate':team,'original_nba_game_id':row['nba_game_id'],'suggested_matchup':proposed,'suggested_nba_game_id':GAMES.get(proposed,''),'mapping_resolution':resolution,'reason':reason,'source_page':row['source_page'],'source_pdf_context':row['source_pdf_context'],'player_identity':'NOT_CERTIFIED','injury_status_evidence':'NOT_CERTIFIED','historical_asof':'NOT_CERTIFIED','training_eligible':'NO'}

def run(root, report_path=None):
    root=root.resolve(); report_path=Path(report_path).resolve() if report_path else locate(root)
    if not report_path.is_relative_to(root):raise ValueError('Report must be inside project')
    report=json.loads(report_path.read_text(encoding='utf-8'))
    if report.get('milestone')!='S8.22.10.14' or report.get('records_total')!=54 or report.get('training_decision')!='BLOCK_TRAINING':raise ValueError('Invalid upstream report')
    triage_path=report_path.parent/'injury_evidence_triage.csv'; exceptions_path=report_path.parent/'exception_queue.csv'
    if not triage_path.is_file() or not exceptions_path.is_file():raise FileNotFoundError('Upstream triage or exception CSV missing')
    triage=csv_read(triage_path); exceptions=csv_read(exceptions_path)
    if len(triage)!=54 or len(exceptions)!=4 or len({r['record_id'] for r in triage})!=54:raise ValueError('Unexpected row counts or duplicate IDs')
    if {r['record_id'] for r in exceptions}!={r['record_id'] for r in triage if r['triage_status']=='EXCEPTION_REVIEW_REQUIRED'}:raise ValueError('Exception queue differs from triage')
    if any('GAME_MAPPING_UNVERIFIED' not in r['triage_reasons'].split('|') for r in exceptions):raise ValueError('Unexpected exception reason; investigate separately')
    if any(r['game_id_evidence']!='UNVERIFIED' for r in exceptions):raise ValueError('Exception unexpectedly verified')
    rows=[classify(r) for r in exceptions]
    token=hashlib.sha256((sha(triage_path)+sha(exceptions_path)).encode()).hexdigest()[:16]
    out=root/f'research/p0_s8/s8_22_10_15/results/{DATE}/{token}';out.mkdir(parents=True,exist_ok=True)
    with (out/'mapping_exception_analysis.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    summary={'milestone':'S8.22.10.15','game_date':DATE,'source_report':str(report_path),'source_triage_sha256':sha(triage_path),'source_exception_sha256':sha(exceptions_path),'total_original_rows':54,'mapping_exceptions_analyzed':len(rows),'resolution_counts':dict(Counter(r['mapping_resolution'] for r in rows)),'reason_counts':dict(Counter(r['reason'] for r in rows)),'resolved_in_source_ledger':0,'injury_rows_certified':0,'historical_asof':'NOT_CERTIFIED','player_identity':'NOT_CERTIFIED','research_status':'RESEARCH_ONLY','training_decision':'BLOCK_TRAINING','note':'Suggestions are not modifications or certifications. Only same-date uniquely matched teams with no conflicting matchup are deterministic candidates. No original files modified.'}
    (out/'review.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',out/'review.json');print(json.dumps(summary,indent=2))
    print('EXCEPTIONS:')
    for r in rows:print(f"  {r['record_id']}: team={r['team_candidate']} matchup={r['matchup_candidate'] or '<blank>'} -> {r['suggested_matchup'] or '<none>'} [{r['mapping_resolution']}: {r['reason']}]")
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project-root',default='.');p.add_argument('--report');a=p.parse_args()
    try:run(Path(a.project_root),a.report)
    except (ValueError,KeyError,OSError) as exc:p.exit(2,'FAIL CLOSED: '+str(exc)+'\n')
if __name__=='__main__':main()
