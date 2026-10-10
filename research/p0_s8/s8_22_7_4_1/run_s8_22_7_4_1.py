"""S8.22.7.4.1: offline independent announcement comparison (never certifies as-of)."""
import argparse
import csv
import hashlib
import html
import json
import re
import uuid
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.ignored=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','noscript'): self.ignored+=1
    def handle_endtag(self, tag):
        if tag in ('script','style','noscript') and self.ignored: self.ignored-=1
    def handle_data(self, data):
        if not self.ignored: self.parts.append(data)

def normalize_text(value):
    return ' '.join(html.unescape(value).replace('\xa0',' ').split()).casefold()

def extract_visible(data):
    parser=VisibleText(); parser.feed(data.decode('utf-8',errors='replace'))
    return normalize_text(' '.join(parser.parts))

def read_csv(path, required):
    with Path(path).open(newline='',encoding='utf-8-sig') as f:
        r=csv.DictReader(f)
        if not r.fieldnames or not set(required).issubset(r.fieldnames):
            raise ValueError('MISSING_REQUIRED_COLUMNS')
        return list(r)

def validate_rows(rows,date,quote_required=False):
    if not rows: raise ValueError('EMPTY_ROWS_NOT_NO_GAME_EVIDENCE')
    ids=set()
    for r in rows:
        gid=r['official_nba_game_id']
        if r['game_date']!=date or not re.fullmatch(r'00\d{8}',gid): raise ValueError('BAD_DATE_OR_GAME_ID')
        if gid in ids: raise ValueError('DUPLICATE_GAME_ID')
        ids.add(gid)
        if not re.fullmatch('[A-Z]{2,3}',r['home_team']) or not re.fullmatch('[A-Z]{2,3}',r['away_team']) or r['home_team']==r['away_team']:
            raise ValueError('BAD_TEAMS')
        dt=datetime.fromisoformat(r['tipoff_utc'].replace('Z','+00:00'))
        if dt.tzinfo is None or dt.utcoffset()!=timezone.utc.utcoffset(dt): raise ValueError('TIPOFF_NOT_UTC')
        if quote_required and (not r['matchup_quote'].strip() or not r['tipoff_quote'].strip()):
            raise ValueError('SOURCE_QUOTES_REQUIRED')
    return {r['official_nba_game_id']:r for r in rows}

def archive(root,date,receipt_path):
    root=Path(root).resolve(); rp=Path(receipt_path).resolve()
    if not rp.is_relative_to(root): raise ValueError('RECEIPT_OUTSIDE_PROJECT')
    rec=json.loads(rp.read_text(encoding='utf-8'))
    if rec.get('date')!=date: raise ValueError('RECEIPT_DATE_MISMATCH')
    url=urlsplit(rec['source_url'])
    if url.scheme!='https' or url.hostname not in ('nba.com','www.nba.com') or url.username or url.password or url.port not in (None,443):
        raise ValueError('NON_OFFICIAL_URL')
    relative=Path(rec['evidence_path'])
    if relative.is_absolute() or '..' in relative.parts: raise ValueError('UNSAFE_EVIDENCE_PATH')
    p=(root/relative).resolve()
    if not p.is_relative_to(root) or not p.is_file(): raise ValueError('MISSING_ARCHIVE')
    data=p.read_bytes()
    if hashlib.sha256(data).hexdigest()!=rec['sha256'] or len(data)!=rec['bytes']:
        raise ValueError('ARCHIVE_INTEGRITY_FAILURE')
    retrieved=datetime.fromisoformat(rec['retrieved_utc'].replace('Z','+00:00'))
    if retrieved.tzinfo is None: raise ValueError('RECEIPT_TIMEZONE_REQUIRED')
    return rec,extract_visible(data)

def audit(root,date,receipt_path,reviewed_csv,reference_csv):
    root=Path(root).resolve()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date): raise ValueError('BAD_DATE')
    rec,visible=archive(root,date,receipt_path)
    reviewed=read_csv(reviewed_csv,('game_date','official_nba_game_id','home_team','away_team','tipoff_utc','matchup_quote','tipoff_quote'))
    reference=read_csv(reference_csv,('game_date','official_nba_game_id','home_team','away_team','tipoff_utc'))
    a=validate_rows(reviewed,date,quote_required=True); b=validate_rows(reference,date)
    unsupported=[]
    for r in reviewed:
        for field in ('matchup_quote','tipoff_quote'):
            # Quotes are verified against *visible* HTML, not navigation scripts.
            if normalize_text(r[field]) not in visible:
                unsupported.append({'game_id':r['official_nba_game_id'],'field':field})
    missing=sorted(a.keys()-b.keys()); extra=sorted(b.keys()-a.keys())
    conflicts=[]
    for gid in sorted(a.keys()&b.keys()):
        for key in ('home_team','away_team'):
            if a[gid][key]!=b[gid][key]:conflicts.append({'game_id':gid,'field':key})
        dt_a=datetime.fromisoformat(a[gid]['tipoff_utc'].replace('Z','+00:00'))
        dt_b=datetime.fromisoformat(b[gid]['tipoff_utc'].replace('Z','+00:00'))
        if abs((dt_a-dt_b).total_seconds())>300:conflicts.append({'game_id':gid,'field':'tipoff_utc'})
    # Require a human-specified claim of date coverage, with exact source quote.
    coverage_quote=reviewed[0].get('date_coverage_quote','').strip()
    if any(r.get('date_coverage_quote','').strip()!=coverage_quote for r in reviewed):
        raise ValueError('INCONSISTENT_COVERAGE_QUOTE')
    coverage_quote_present=bool(coverage_quote) and normalize_text(coverage_quote) in visible
    matched=not (unsupported or missing or extra or conflicts) and coverage_quote_present
    report={'milestone':'S8.22.7.4.1','date':date,'mode':'OFFLINE_ANNOUNCEMENT_REVIEW',
        'date_source_url':rec['source_url'],'date_source_sha256':rec['sha256'],
        'date_source_retrieved_utc':rec['retrieved_utc'],
        'announcement_rows':len(reviewed),'game_reference_rows':len(reference),
        'unsupported_quotes':unsupported,'coverage_quote_present':coverage_quote_present,
        'missing_in_game_reference':missing,'extra_in_game_reference':extra,'conflicts':conflicts,
        'row_set_agreement':matched,
        'status':'CANDIDATE_ANNOUNCEMENT_AGREEMENT_REVIEW_REQUIRED' if matched else 'ANNOUNCEMENT_EVIDENCE_CONFLICT',
        'date_completeness':'NOT_CERTIFIED','historical_asof':'NOT_CERTIFIED',
        'routine_collection_approved':False,'training_eligible':False,'decision':'BLOCK_TRAINING',
        'limitations':['Quotes appearing on a page do not prove that all games are listed',
          'Official game IDs are joined from independently sourced game pages; the announcement need not contain IDs',
          'Manual transcription and coverage interpretation still require human review',
          '2026 retrieval does not prove pregame availability in 2023']}
    out=root/'research/p0_s8/s8_22_7_4_1/results'/date
    out.mkdir(parents=True,exist_ok=True)
    path=out/f'announcement_review_{uuid.uuid4().hex}.json'
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    report['report_path']=path.relative_to(root).as_posix()
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',type=Path,default=Path('.'))
    p.add_argument('--date',required=True)
    p.add_argument('--date-receipt',type=Path,required=True)
    p.add_argument('--reviewed-date-csv',type=Path,required=True)
    p.add_argument('--game-reference-csv',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(audit(a.project_root,a.date,a.date_receipt,a.reviewed_date_csv,a.game_reference_csv),indent=2))
if __name__=='__main__':main()
