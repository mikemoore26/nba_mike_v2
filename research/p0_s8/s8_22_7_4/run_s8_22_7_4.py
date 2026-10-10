"""S8.22.7.4: offline official date-level schedule evidence comparison.

Strictly candidate review: no schedule-completeness certification from retrospective pages.
"""
import argparse
import csv
import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

DATE_RE = re.compile(r'\d{4}-\d{2}-\d{2}\Z')
ID_RE = re.compile(r'00\d{8}\Z')
FIELDS = ['game_date','official_nba_game_id','home_team','away_team','tipoff_utc']
def sha(data): return hashlib.sha256(data).hexdigest()
def read_csv(path, fields):
    with path.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not set(fields).issubset(reader.fieldnames):
            raise ValueError('CSV_COLUMNS_MISSING')
        return list(reader)
def official_url(url):
    u=urlsplit(url)
    if u.scheme!='https' or u.hostname not in ('nba.com','www.nba.com') or u.username or u.password or u.port not in (None,443):
        raise ValueError('OFFICIAL_NBA_URL_REQUIRED')
def evidence(root, receipt_path, date):
    root=root.resolve()
    rp=Path(receipt_path).resolve()
    if not rp.is_relative_to(root): raise ValueError('RECEIPT_OUTSIDE_PROJECT')
    rec=json.loads(rp.read_text(encoding='utf-8'))
    if rec.get('date')!=date: raise ValueError('RECEIPT_DATE_MISMATCH')
    official_url(rec['source_url'])
    rel=Path(rec['evidence_path'])
    if rel.is_absolute() or '..' in rel.parts: raise ValueError('UNSAFE_EVIDENCE_PATH')
    path=(root/rel).resolve()
    if not path.is_relative_to(root) or not path.is_file(): raise ValueError('EVIDENCE_NOT_FOUND')
    content=path.read_bytes()
    if sha(content)!=rec['sha256'] or len(content)!=rec['bytes']:
        raise ValueError('EVIDENCE_INTEGRITY_FAILURE')
    dt=datetime.fromisoformat(rec['retrieved_utc'].replace('Z','+00:00'))
    if dt.tzinfo is None: raise ValueError('NAIVE_RETRIEVAL_TIME')
    return rec,content
def parse_rows(path,date):
    rows=read_csv(path,FIELDS)
    if not rows: raise ValueError('EMPTY_DATE_SCHEDULE_NOT_PROOF_OF_NO_GAMES')
    ids=set()
    for r in rows:
        if r['game_date']!=date or not ID_RE.fullmatch(r['official_nba_game_id']):
            raise ValueError('BAD_GAME_DATE_OR_ID')
        if r['official_nba_game_id'] in ids: raise ValueError('DUPLICATE_GAME_ID')
        ids.add(r['official_nba_game_id'])
        home,away=r['home_team'],r['away_team']
        if not re.fullmatch('[A-Z]{2,3}',home) or not re.fullmatch('[A-Z]{2,3}',away) or home==away:
            raise ValueError('BAD_TEAM')
        t=datetime.fromisoformat(r['tipoff_utc'].replace('Z','+00:00'))
        if t.tzinfo is None: raise ValueError('TIPOFF_TIMEZONE_REQUIRED')
    return rows
def audit(root,date,receipt_path,reviewed_schedule,reference_path):
    root=Path(root).resolve()
    if not DATE_RE.fullmatch(date): raise ValueError('BAD_DATE')
    rec,content=evidence(root,receipt_path,date)
    schedule=parse_rows(Path(reviewed_schedule),date)
    reference=parse_rows(Path(reference_path),date)
    # Every claimed schedule ID must be observable in the preserved source.
    # This is necessary but not sufficient to prove the webpage contains a full-day schedule.
    missing_in_source=[r['official_nba_game_id'] for r in schedule if r['official_nba_game_id'].encode() not in content]
    ids_schedule={r['official_nba_game_id']:r for r in schedule}
    ids_reference={r['official_nba_game_id']:r for r in reference}
    missing_reference=sorted(ids_schedule.keys()-ids_reference.keys())
    extra_reference=sorted(ids_reference.keys()-ids_schedule.keys())
    conflicts=[]
    for game_id in sorted(ids_schedule.keys()&ids_reference.keys()):
        s,r=ids_schedule[game_id],ids_reference[game_id]
        for key in ('home_team','away_team'):
            if s[key]!=r[key]: conflicts.append({'game_id':game_id,'field':key,'date_level':s[key],'game_level':r[key]})
        a=datetime.fromisoformat(s['tipoff_utc'].replace('Z','+00:00'))
        b=datetime.fromisoformat(r['tipoff_utc'].replace('Z','+00:00'))
        if abs((a-b).total_seconds())>300:
            conflicts.append({'game_id':game_id,'field':'tipoff_utc','date_level':s['tipoff_utc'],'game_level':r['tipoff_utc']})
    consistent=not (missing_in_source or missing_reference or extra_reference or conflicts)
    result={
        'milestone':'S8.22.7.4','date':date,'mode':'OFFLINE_DATE_LEVEL_REVIEW',
        'date_source_url':rec['source_url'],'date_source_sha256':rec['sha256'],
        'date_source_retrieved_utc':rec['retrieved_utc'],
        'date_level_rows':len(schedule),'individual_reference_rows':len(reference),
        'missing_game_ids_in_archived_date_source':missing_in_source,
        'missing_from_individual_reference':missing_reference,
        'extra_in_individual_reference':extra_reference,'field_conflicts':conflicts,
        'row_set_agreement':consistent,
        'status':'CANDIDATE_DATE_LEVEL_AGREEMENT_REVIEW_REQUIRED' if consistent else 'DATE_LEVEL_EVIDENCE_CONFLICT',
        'source_claims_complete_date':'NOT_INDEPENDENTLY_ESTABLISHED',
        'date_completeness':'NOT_CERTIFIED','historical_asof':'NOT_CERTIFIED',
        'routine_collection_approved':False,'training_eligible':False,'decision':'BLOCK_TRAINING',
        'limitations':['A page containing all supplied IDs may still omit other games',
                       'Manual transcription and source completeness require independent human review',
                       'Retrospective evidence does not establish historical pregame availability']
    }
    dest=root/'research/p0_s8/s8_22_7_4/results'/date
    dest.mkdir(parents=True,exist_ok=True)
    token=uuid.uuid4().hex
    report=dest/f'date_completeness_review_{token}.json'
    report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    result['report_path']=report.relative_to(root).as_posix()
    return result
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',type=Path,default=Path('.'))
    p.add_argument('--date',required=True)
    p.add_argument('--date-receipt',type=Path,required=True)
    p.add_argument('--reviewed-date-csv',type=Path,required=True)
    p.add_argument('--game-reference-csv',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(audit(a.project_root,a.date,a.date_receipt,a.reviewed_date_csv,a.game_reference_csv),indent=2))
if __name__=='__main__': main()
