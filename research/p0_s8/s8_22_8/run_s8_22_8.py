"""Offline, fail-closed historical pregame data feasibility audit. No network calls."""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

CATEGORIES = {
    'player_availability': 'Pre-tipoff roster eligibility, injury designation, DNP risk and publication time',
    'expected_minutes': 'Pregame minutes projection inputs, never final box-score minutes',
    'starting_lineups': 'Lineup announcement and timestamp before selected prediction cutoff',
    'player_opportunity': 'Prior-game-only usage, role and opportunity with point-in-time joins',
    'betting_markets': 'Historical player prop line, odds, book and observed timestamp',
}
REQUIRED = ('category','source_name','source_url','evidence_path','sha256','observed_utc','event_tipoff_utc','coverage_start','coverage_end','license_status','reviewer','notes')

def parse_time(s):
    if not s: return None
    try:
        dt = datetime.fromisoformat(s.replace('Z','+00:00'))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except ValueError: return None

def audit(project_root, manifest):
    root = Path(project_root).resolve()
    with Path(manifest).open(newline='', encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or any(x not in reader.fieldnames for x in REQUIRED):
            raise ValueError('Manifest missing required columns: '+', '.join(x for x in REQUIRED if x not in (reader.fieldnames or [])))
        rows=list(reader)
    results={k:{'description':v,'evidence_rows':0,'integrity_pass_rows':0,'pregame_timestamp_rows':0,'licensing_reviewed_rows':0,'status':'NOT_ESTABLISHED','findings':[]} for k,v in CATEGORIES.items()}
    findings=[]
    for n,row in enumerate(rows,2):
        cat=row['category'].strip()
        if not cat:
            if any((v or '').strip() for v in row.values()): findings.append(f'row {n}: category missing')
            continue
        if cat not in results:
            findings.append(f'row {n}: unknown category {cat}'); continue
        rec=results[cat]; rec['evidence_rows']+=1
        issues=[]
        for key in ('source_name','source_url','evidence_path','sha256','reviewer'):
            if not row[key].strip(): issues.append(f'{key} missing')
        p=Path(row['evidence_path'].strip())
        if p.is_absolute() or '..' in p.parts: issues.append('evidence path must be relative within project')
        else:
            actual=(root/p).resolve()
            if not actual.is_relative_to(root): issues.append('evidence path escapes project')
            elif not actual.is_file(): issues.append('evidence file missing')
            elif hashlib.sha256(actual.read_bytes()).hexdigest().lower()!=row['sha256'].strip().lower(): issues.append('SHA256 mismatch')
        if not issues: rec['integrity_pass_rows']+=1
        observed=parse_time(row['observed_utc'].strip()); tipoff=parse_time(row['event_tipoff_utc'].strip())
        if observed and tipoff and observed < tipoff and not issues: rec['pregame_timestamp_rows']+=1
        else: issues.append('historical pre-tipoff observation not verified')
        if row['license_status'].strip().upper() == 'REVIEWED_PERMITTED': rec['licensing_reviewed_rows']+=1
        else: issues.append('license not reviewed/permitted')
        if issues: rec['findings'].append({'row':n,'issues':issues})
    for cat,rec in results.items():
        if rec['evidence_rows'] and rec['integrity_pass_rows']==rec['evidence_rows'] and rec['pregame_timestamp_rows']==rec['evidence_rows'] and rec['licensing_reviewed_rows']==rec['evidence_rows']:
            rec['status']='CANDIDATE_MANUAL_REVIEW_REQUIRED'
    return {'milestone':'S8.22.8','generated_utc':datetime.now(timezone.utc).isoformat(),'scope':'HISTORICAL_PREGAME_FEASIBILITY','manifest_sha256':hashlib.sha256(Path(manifest).read_bytes()).hexdigest(),'categories':results,'manifest_findings':findings,'retrospective_schedule_completeness':'NOT_CERTIFIED','historical_asof':'NOT_CERTIFIED','routine_collection_approved':False,'training_eligible':False,'decision':'BLOCK_TRAINING','next_action':'Review evidence gaps and manually select a permitted point-in-time source; do not train.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root',required=True); ap.add_argument('--manifest',required=True); args=ap.parse_args()
    result=audit(args.project_root,args.manifest)
    dest=Path(args.project_root)/'research/p0_s8/s8_22_8/results'; dest.mkdir(parents=True,exist_ok=True)
    out=dest/('feasibility_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',out)
    for cat,rec in result['categories'].items(): print(f'{cat}: {rec["status"]} (evidence={rec["evidence_rows"]}, pregame_verified={rec["pregame_timestamp_rows"]})')
    print('DECISION:',result['decision'])
    if result['manifest_findings']: print('MANIFEST FINDINGS:',result['manifest_findings'])
if __name__=='__main__': main()
