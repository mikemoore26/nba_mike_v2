"""S7.26: provenance-preserving dated transaction chronology, no inferred verified roster."""
import argparse,csv,hashlib,json,re
from collections import defaultdict
from datetime import date,datetime,timezone
from pathlib import Path

FIELDS=('player_id','player_name','effective_date','event_type','from_team','to_team','source_name','source_url','source_document_sha256','source_published_utc','retrieved_utc','evidence_id')
EVENTS={'SIGN','WAIVE','TRADE','RELEASE','CONTRACT_END','TWO_WAY_SIGN','CONVERT','TEN_DAY_SIGN','TEN_DAY_END'}
TEAMS={'ATL','BOS','BKN','CHA','CHI','CLE','DAL','DEN','DET','GSW','HOU','IND','LAC','LAL','MEM','MIA','MIL','MIN','NOP','NYK','OKC','ORL','PHI','PHX','POR','SAC','SAS','TOR','UTA','WAS'}
SHA=re.compile(r'^[0-9a-f]{64}$')
def validate(row):
    if not row['player_id'].strip().isdigit() or not row['player_name'].strip():return 'INVALID_IDENTITY'
    try:date.fromisoformat(row['effective_date'])
    except ValueError:return 'INVALID_DATE'
    if row['event_type'] not in EVENTS:return 'INVALID_EVENT'
    for field in ('from_team','to_team'):
        if row[field] and row[field] not in TEAMS:return 'INVALID_TEAM'
    if row['event_type']=='TRADE' and (not row['from_team'] or not row['to_team'] or row['from_team']==row['to_team']):return 'INVALID_TRANSFER'
    if row['event_type'] in {'SIGN','TWO_WAY_SIGN','TEN_DAY_SIGN','CONVERT'} and not row['to_team']:return 'MISSING_DESTINATION'
    if row['event_type'] in {'WAIVE','RELEASE','CONTRACT_END','TEN_DAY_END'} and not row['from_team']:return 'MISSING_ORIGIN'
    if not row['source_name'].strip() or not row['source_url'].startswith('https://') or not SHA.fullmatch(row['source_document_sha256']):return 'MISSING_SOURCE_PROVENANCE'
    try:
        published=datetime.fromisoformat(row['source_published_utc'].replace('Z','+00:00'))
        retrieved=datetime.fromisoformat(row['retrieved_utc'].replace('Z','+00:00'))
        if published.tzinfo is None or retrieved.tzinfo is None or published>retrieved:return 'INVALID_SOURCE_TIMES'
    except ValueError:return 'INVALID_SOURCE_TIMES'
    if not row['evidence_id'].strip():return 'MISSING_EVIDENCE_ID'
    return None

def process(source,out):
    source=Path(source);out=Path(out)
    raw=source.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    with source.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames is None or set(reader.fieldnames)!=set(FIELDS):raise ValueError('Transaction CSV schema mismatch')
        rows=list(reader)
    checked=[];seen=set()
    for i,row in enumerate(rows,2):
        reason=validate(row)
        if not reason and row['evidence_id'] in seen:reason='DUPLICATE_EVIDENCE_ID'
        seen.add(row['evidence_id'])
        checked.append(dict(row,source_row=i,validation=reason or 'VALID'))
    valid=[x for x in checked if x['validation']=='VALID']
    groups=defaultdict(list)
    for row in valid:groups[(row['player_id'],row['effective_date'])].append(row)
    conflicts=set()
    for group in groups.values():
        transitions={(x['event_type'],x['from_team'],x['to_team']) for x in group}
        if len(transitions)>1:
            conflicts.update(x['source_row'] for x in group)
    for row in checked:
        if row['source_row'] in conflicts:row['validation']='SAME_DAY_CONFLICT'
    accepted=sorted((x for x in checked if x['validation']=='VALID'),key=lambda x:(x['player_id'],x['effective_date'],x['source_row']))
    # A transaction is an event, NOT a validated continuous roster interval.
    out.mkdir(parents=True,exist_ok=True)
    with (out/'s7_26_chronology.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(FIELDS)+['source_row','validation']);w.writeheader();w.writerows(accepted)
    with (out/'s7_26_review.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(FIELDS)+['source_row','validation']);w.writeheader();w.writerows(x for x in checked if x['validation']!='VALID')
    report={'milestone':'S7.26','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','input_sha256':digest,'input_rows':len(rows),'accepted_events':len(accepted),'review_required':len(checked)-len(accepted),'same_day_conflict_rows':len(conflicts),'date_specific_verified_assignments':0,'roster_intervals_promoted':0,'historical_publication_verified':False,'eligible_for_asof_training':False,'note':'Source assertions and chronology only. CSV input is not authenticated by this script; no continuous membership or historical as-of publication inferred.'}
    (out/'s7_26_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--input-csv',default='research/p0_s4/s7_26/transaction_evidence.csv');p.add_argument('--output-dir',default='research/p0_s4/s7_26/results');a=p.parse_args()
    try:print(json.dumps(process(a.input_csv,a.output_dir),indent=2))
    except (OSError,ValueError,KeyError) as e:
        print(json.dumps({'milestone':'S7.26','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(e)}));raise SystemExit(1)
if __name__=='__main__':main()
