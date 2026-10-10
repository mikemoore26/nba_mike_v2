"""S8.22.7.1 date-specific, immutable manual BALLDONTLIE schedule capture."""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json,os,uuid
from datetime import date,datetime,timezone
from pathlib import Path

FIELDS=['provider','provider_game_id','official_nba_game_id','game_date','home_provider_team_id','away_provider_team_id','tipoff_utc','tipoff_status','game_status']
MANIFEST_FIELDS=['date','phase','provider_csv','reference_csv','selection_reason']

def module_at(path, name):
    if not path.is_file(): raise FileNotFoundError(str(path))
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def sha(b):return hashlib.sha256(b).hexdigest()

def update_manifest(root, game_date, csv_path):
    path=root/'research/p0_s8/s8_22_7/date_manifest.csv'
    if not path.is_file():return 'MANIFEST_MISSING'
    with path.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not set(MANIFEST_FIELDS).issubset(reader.fieldnames):return 'MANIFEST_SCHEMA_UNSUPPORTED'
        fields=reader.fieldnames;rows=list(reader)
    matches=[r for r in rows if r['date']==game_date]
    if len(matches)!=1:return 'DATE_NOT_UNIQUE_IN_MANIFEST'
    target=matches[0]
    old=target['provider_csv'].strip()
    if old:
        existing=root/old
        if existing.is_file():return 'EXISTING_PROVIDER_SNAPSHOT_PRESERVED'
        # Do not silently replace even broken/missing links.
        return 'EXISTING_MANIFEST_VALUE_PRESERVED'
    target['provider_csv']=csv_path.relative_to(root).as_posix()
    import io
    out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
    # Only update a manifest after successful capture. Retain prior bytes as a backup.
    backup=path.with_name(path.name+'.pre_s82271.bak')
    if not backup.exists():backup.write_bytes(path.read_bytes())
    tmp=path.with_name(path.name+'.s82271.tmp')
    tmp.write_text(out.getvalue(),encoding='utf-8');os.replace(tmp,path)
    return 'UPDATED'

def run(root, game_date, *, fixture=None, live=False, checkpoint='T-24H', update=False, fetcher=None):
    root=Path(root).resolve()
    if date.fromisoformat(game_date).isoformat()!=game_date:raise ValueError('INVALID_DATE')
    if live == (fixture is not None):raise ValueError('CHOOSE_LIVE_OR_FIXTURE')
    if fixture is not None:
        fixture=Path(fixture).resolve()
        if not fixture.is_file() or fixture.stat().st_size>3_000_000:raise ValueError('INVALID_FIXTURE')
    adapter=module_at(root/'research/p0_s8/s8_22_4/run_s8_22_4.py','s8224_for_2271')
    s821=adapter.load_s821(root)
    if checkpoint not in s821.CHECKPOINTS:raise ValueError('INVALID_CHECKPOINT')
    if live:
        key=adapter.load_key(root)
        body,status,error,url,headers=(fetcher or adapter.fetch)(key,game_date)
        mode='LIVE_MANUAL'
    else:
        body=fixture.read_bytes();status=200;error=None;url='fixture://balldontlie/games';headers={};mode='OFFLINE_FIXTURE'
    if body is not None and len(body)>3_000_000:body=None;error='BODY_TOO_LARGE'
    # S8.21 remains the authoritative raw-response ledger.
    event=s821.capture(root/'research/p0_s8/s8_21/artifacts',kind='schedule',url=url,checkpoint=checkpoint,
                       payload=body,game_id='',http_status=status,error_code=error)
    games=[];parse_status='NOT_ATTEMPTED' if error else 'PASS'
    if not error:
        try:games=adapter.parse_games(body,game_date)
        except (ValueError,TypeError) as exc:parse_status=str(exc);games=[]
    # Every attempt gets a distinct directory; existing evidence is never overwritten.
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    capture_id=stamp+'_'+uuid.uuid4().hex[:12]
    parent=root/'research/p0_s8/s8_22_7_1/captures'/game_date
    dest=parent/capture_id;dest.mkdir(parents=True,exist_ok=False)
    csv_path=dest/'provider_games.csv'
    with csv_path.open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(games)
    valid=error is None and parse_status=='PASS' and event.get('outcome') in ('SUCCESS','DUPLICATE')
    state=('CAPTURE_FAILED' if not valid else 'EMPTY_SCHEDULE_UNVERIFIED' if not games else 'PROVIDER_GAMES_PRESENT_UNVERIFIED')
    report={'milestone':'S8.22.7.1','date':game_date,'capture_id':capture_id,'mode':mode,'checkpoint':checkpoint,
            'http_status':status,'retrieval_error':error,'parse_status':parse_status,'provider_rows':len(games),
            'schedule_state':state,'source_url':url,'response_headers_allowlisted':headers,
            's821_event_id':event.get('event_id'),'s821_outcome':event.get('outcome'),
            's821_raw_sha256':event.get('sha256'),'provider_csv_sha256':sha(csv_path.read_bytes()),
            'manifest_status':'NOT_REQUESTED','reference_status':'NOT_ACQUIRED',
            'historical_asof_availability':'NOT_CERTIFIED','routine_collection_approved':False,
            'training_eligible':False,'status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING'}
    if update and valid:
        report['manifest_status']=update_manifest(root,game_date,csv_path)
    elif update:report['manifest_status']='NOT_UPDATED_CAPTURE_FAILED'
    (dest/'capture_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    # Fail-closed report, even for an empty but parseable schedule.
    return report,dest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',type=Path,default=Path('.'));p.add_argument('--date',required=True)
    p.add_argument('--checkpoint',default='T-24H');p.add_argument('--update-manifest',action='store_true')
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--live',action='store_true');g.add_argument('--fixture',type=Path)
    a=p.parse_args();report,dest=run(a.project_root,a.date,fixture=a.fixture,live=a.live,
                                       checkpoint=a.checkpoint,update=a.update_manifest)
    print(json.dumps({'capture_dir':str(dest),'schedule_state':report['schedule_state'],
                      'provider_rows':report['provider_rows'],'manifest_status':report['manifest_status'],
                      'decision':report['decision']},indent=2))
    if report['schedule_state']=='CAPTURE_FAILED':raise SystemExit(2)
if __name__=='__main__':main()
