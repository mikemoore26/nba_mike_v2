"""S8.22.7.2: archive independently acquired NBA evidence; fail closed."""
import argparse,csv,hashlib,json,re,shutil,urllib.request,urllib.parse,uuid
from datetime import datetime,timezone
from pathlib import Path

FIELDS=['game_date','official_nba_game_id','home_team','away_team','tipoff_utc','source_url','evidence_sha256','evidence_retrieved_utc']
ALLOWED_HOSTS={'www.nba.com','nba.com'}
MAX_BYTES=5_000_000
def sha(b): return hashlib.sha256(b).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat()
def safe_url(url):
    u=urllib.parse.urlsplit(url)
    if u.scheme!='https' or u.hostname not in ALLOWED_HOSTS or u.username or u.password or u.port not in (None,443):
        raise ValueError('OFFICIAL_NBA_HTTPS_URL_REQUIRED')
    return url
def archive_bytes(root,date,source_url,content,receipt=None):
    safe_url(source_url)
    if not content or len(content)>MAX_BYTES: raise ValueError('INVALID_EVIDENCE_SIZE')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date): raise ValueError('INVALID_DATE')
    stamp=receipt or utc()
    d=root/'research/p0_s8/s8_22_7_2/evidence'/date/uuid.uuid4().hex
    d.mkdir(parents=True,exist_ok=False)
    (d/'source.bin').write_bytes(content)
    meta={'date':date,'source_url':source_url,'retrieved_utc':stamp,'sha256':sha(content),'bytes':len(content),
          'evidence_path':str((d/'source.bin').relative_to(root)).replace('\\','/'),
          'source_kind':'NBA_WEB_PAGE_SNAPSHOT','pre_game_publication_verified':False,
          'independent_schedule_completeness_verified':False}
    (d/'receipt.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    return meta
def fetch(root,date,url):
    safe_url(url)
    req=urllib.request.Request(url,headers={'User-Agent':'NBA-MIKE-v2-research/0.1','Accept':'text/html,application/json'})
    with urllib.request.urlopen(req,timeout=20) as r:
        if safe_url(r.geturl()) != r.geturl(): raise ValueError('UNSAFE_REDIRECT')
        data=r.read(MAX_BYTES+1)
        if r.status!=200: raise ValueError('HTTP_NOT_200')
    return archive_bytes(root,date,url,data)
def import_file(root,date,url,path):
    return archive_bytes(root,date,url,Path(path).read_bytes())
def timestamp(v):
    try:
        t=datetime.fromisoformat(v.replace('Z','+00:00'))
        return t if t.tzinfo else None
    except (ValueError,AttributeError): return None
def normalize(root,date,source_receipt,reviewed_rows_csv,allow_empty=False):
    receipt=json.loads(Path(source_receipt).read_text(encoding='utf-8'))
    if receipt.get('date')!=date: raise ValueError('EVIDENCE_DATE_MISMATCH')
    safe_url(receipt['source_url'])
    p=(root/receipt['evidence_path']).resolve()
    if not p.is_relative_to(root.resolve()) or not p.is_file() or sha(p.read_bytes())!=receipt['sha256']:
        raise ValueError('EVIDENCE_HASH_OR_PATH_INVALID')
    if not timestamp(receipt.get('retrieved_utc')): raise ValueError('BAD_RECEIPT_TIME')
    with Path(reviewed_rows_csv).open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not {'game_date','official_nba_game_id','home_team','away_team','tipoff_utc'}.issubset(reader.fieldnames):
            raise ValueError('BAD_REVIEW_CSV_COLUMNS')
        rows=list(reader)
    if not rows: raise ValueError('EMPTY_REFERENCE_NEEDS_SEPARATE_NO_GAME_EVIDENCE')
    ids=set()
    for row in rows:
        if row['game_date']!=date or not re.fullmatch(r'00\d{8}',row['official_nba_game_id'].strip()):
            raise ValueError('INVALID_DATE_OR_OFFICIAL_ID')
        if row['official_nba_game_id'] in ids: raise ValueError('DUPLICATE_OFFICIAL_ID')
        ids.add(row['official_nba_game_id'])
        if not re.fullmatch(r'[A-Z]{2,3}',row['home_team']) or not re.fullmatch(r'[A-Z]{2,3}',row['away_team']) or row['home_team']==row['away_team']:
            raise ValueError('INVALID_TEAM')
        if not timestamp(row['tipoff_utc']): raise ValueError('INVALID_TIPOFF')
        row.update(source_url=receipt['source_url'],evidence_sha256=receipt['sha256'],
                   evidence_retrieved_utc=receipt['retrieved_utc'])
    dest=root/'research/p0_s8/s8_22_7_2/references'/date
    dest.mkdir(parents=True,exist_ok=True)
    target=dest/f'official_reference_{uuid.uuid4().hex}.csv'
    with target.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows([{k:r[k] for k in FIELDS} for r in rows])
    return {'reference_path':str(target.relative_to(root)).replace('\\','/'),'reference_sha256':sha(target.read_bytes()),
            'rows':len(rows),'evidence_sha256':receipt['sha256'],'status':'CURATED_REFERENCE_REVIEW_REQUIRED',
            'independent_completeness_verified':False,'training_eligible':False}
def update_manifest(root,date,reference_path):
    manifest=root/'research/p0_s8/s8_22_7/date_manifest.csv'
    with manifest.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f); cols=reader.fieldnames; rows=list(reader)
    if not cols or 'reference_csv' not in cols: raise ValueError('INVALID_MANIFEST')
    hits=[r for r in rows if r['date']==date]
    if len(hits)!=1: raise ValueError('DATE_NOT_UNIQUE_IN_MANIFEST')
    if hits[0]['reference_csv'].strip(): raise ValueError('REFERENCE_ALREADY_SET_NO_OVERWRITE')
    if not (root/reference_path).is_file() or '..' in Path(reference_path).parts or Path(reference_path).is_absolute():
        raise ValueError('UNSAFE_REFERENCE_PATH')
    hits[0]['reference_csv']=reference_path
    tmp=manifest.with_suffix('.csv.tmp')
    with tmp.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
    tmp.replace(manifest)
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--project-root',type=Path,default=Path('.'))
    sub=p.add_subparsers(dest='command',required=True)
    for name in ('fetch','import'):
        q=sub.add_parser(name);q.add_argument('--date',required=True);q.add_argument('--url',required=True)
        if name=='import':q.add_argument('--file',required=True,type=Path)
        else:q.add_argument('--acknowledge-provider-terms',action='store_true')
    q=sub.add_parser('normalize');q.add_argument('--date',required=True);q.add_argument('--receipt',required=True,type=Path)
    q.add_argument('--reviewed-csv',required=True,type=Path);q.add_argument('--update-manifest',action='store_true');q.add_argument('--confirm-full-date-reference',action='store_true')
    a=p.parse_args();root=a.project_root.resolve()
    if a.command=='fetch':
        if not a.acknowledge_provider_terms: raise SystemExit('Explicit --acknowledge-provider-terms required')
        result=fetch(root,a.date,a.url)
    elif a.command=='import':result=import_file(root,a.date,a.url,a.file)
    else:
        result=normalize(root,a.date,a.receipt,a.reviewed_csv)
        if a.update_manifest:
            if not a.confirm_full_date_reference: raise SystemExit('FULL_DATE_REFERENCE_CONFIRMATION_REQUIRED; normalized file created but manifest unchanged')
            update_manifest(root,a.date,result['reference_path'])
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
