"""S7.23 independent roster evidence gate. Never treats PDF section events as roster proof."""
import argparse,csv,json,re
from collections import Counter
from datetime import date
from pathlib import Path

EVIDENCE_FIELDS=('player_id','player_name','team','valid_from','valid_through','source_name','source_url','retrieved_utc','source_asof_utc','evidence_id','independent_of_injury_pdf')
OUTPUT_FIELDS=('source_sha256','record_id','player','reported_team','game_date','verdict','reason','matching_evidence_ids','conflicting_evidence_ids')

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def name_key(s):
    return re.sub(r'[^a-z0-9]','',str(s).casefold())

def parse_day(value):
    try:return date.fromisoformat(value)
    except (TypeError,ValueError):return None

def evidence_valid(e, day):
    start=parse_day(e.get('valid_from')); end=parse_day(e.get('valid_through'))
    if not start or not end or not day or not (start<=day<=end):return False
    if e.get('independent_of_injury_pdf','').strip().lower()!='true':return False
    if not all(e.get(k,'').strip() for k in ('source_name','source_url','retrieved_utc','source_asof_utc','evidence_id','team')):return False
    if not e['source_url'].startswith('https://'):return False
    if not (e.get('player_id','').strip() or e.get('player_name','').strip()):return False
    return True

def verify(row,evidence):
    day=parse_day(row.get('game_date')); name=name_key(row.get('player',''))
    # Never resolve an ambiguous name when multiple player IDs are present.
    matches=[e for e in evidence if evidence_valid(e,day) and name and name_key(e.get('player_name',''))==name]
    ids={e['player_id'].strip() for e in matches if e.get('player_id','').strip()}
    if len(ids)>1:return 'UNRESOLVED','AMBIGUOUS_PLAYER_ID',[],[]
    supporting=[e for e in matches if e['team'].strip()==row.get('team','').strip()]
    opposing=[e for e in matches if e['team'].strip()!=row.get('team','').strip()]
    if supporting and opposing: verdict,reason='CONFLICT','CONTRADICTORY_ROSTER_EVIDENCE'
    elif opposing: verdict,reason='CONFLICT','TEAM_DISAGREES_WITH_INDEPENDENT_ROSTER'
    elif supporting: verdict,reason='VERIFIED','INDEPENDENT_ROSTER_MATCH'
    else: verdict,reason='UNRESOLVED','NO_QUALIFYING_INDEPENDENT_EVIDENCE'
    return verdict,reason,[e['evidence_id'] for e in supporting],[e['evidence_id'] for e in opposing]

def audit(candidates_dir,evidence_path,output_dir):
    candidates_dir=Path(candidates_dir); evidence_path=Path(evidence_path); output_dir=Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    evidence=read_csv(evidence_path) if evidence_path.is_file() else []
    rows=[]; sources=sorted(candidates_dir.glob('*.s7_14_candidates.csv'))
    for path in sources:
        sha=path.name.split('.')[0]
        for row in read_csv(path):
            verdict,reason,support,oppose=verify(row,evidence)
            rows.append(dict(source_sha256=sha,record_id=row.get('record_id',''),player=row.get('player',''),reported_team=row.get('team',''),game_date=row.get('game_date',''),verdict=verdict,reason=reason,matching_evidence_ids='|'.join(support),conflicting_evidence_ids='|'.join(oppose)))
    with (output_dir/'s7_23_roster_checks.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=OUTPUT_FIELDS);writer.writeheader();writer.writerows(rows)
    counts=Counter(r['verdict'] for r in rows)
    report={'milestone':'S7.23','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','report_count':len(sources),'records':len(rows),'evidence_rows':len(evidence),'verified':counts['VERIFIED'],'conflict':counts['CONFLICT'],'unresolved':counts['UNRESOLVED'],'roster_gate':'NO_INDEPENDENT_EVIDENCE' if not evidence else 'EVIDENCE_REVIEW_REQUIRED','historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['Roster evidence must be collected independently of injury PDF; empty template does not verify any players','Name-only matching is provisional; independent stable player IDs and historical date coverage required before promotion','Even verified roster membership does not establish historical injury PDF publication time','No source candidate records modified']}
    (output_dir/'s7_23_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidates-dir',default='research/p0_s4/s7_14/results');p.add_argument('--evidence',default='research/p0_s4/s7_23/roster_evidence.csv');p.add_argument('--output-dir',default='research/p0_s4/s7_23/results');a=p.parse_args()
    print(json.dumps(audit(a.candidates_dir,a.evidence,a.output_dir),indent=2))
if __name__=='__main__':main()
