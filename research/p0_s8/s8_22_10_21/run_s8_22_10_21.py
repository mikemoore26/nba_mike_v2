"""S8.22.10.21: provenance-preserving NBA Stats registry acquisition, no certification."""
import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SEASON='2023-24'
BASE='https://stats.nba.com/stats/commonallplayers'
PARAMS={'LeagueID':'00','Season':SEASON,'IsOnlyCurrentSeason':'0'}
MAX_BYTES=12_000_000

def sha(data):return hashlib.sha256(data).hexdigest()

def url():return BASE+'?'+urllib.parse.urlencode(PARAMS)

def validate(raw):
    from importlib.util import spec_from_file_location,module_from_spec
    stage=Path(__file__).resolve().parents[1]/'s8_22_10_20'/'run_s8_22_10_20.py'
    if not stage.is_file():raise ValueError('S8.22.10.20 parser missing')
    spec=spec_from_file_location('s8221020_parser',stage);mod=module_from_spec(spec);spec.loader.exec_module(mod)
    obj=json.loads(raw.decode('utf-8-sig'))
    rows=mod.parse_registry(obj)
    ids={}
    for row in rows:
        pid=row['id'];name=row['name']
        if pid in ids and ids[pid]!=name:raise ValueError('Conflicting display names for NBA person ID '+pid)
        ids[pid]=name
    return len(rows),len(ids)

def fetch(timeout=20):
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
             'Referer':'https://www.nba.com/','Origin':'https://www.nba.com','Accept':'application/json, text/plain, */*'}
    req=urllib.request.Request(url(),headers=headers,method='GET')
    with urllib.request.urlopen(req,timeout=timeout) as response:
        final=response.geturl()
        if urllib.parse.urlsplit(final).hostname!='stats.nba.com' or urllib.parse.urlsplit(final).scheme!='https':
            raise ValueError('Unexpected redirect host or scheme')
        body=response.read(MAX_BYTES+1)
        if len(body)>MAX_BYTES:raise ValueError('Response exceeds size limit')
        if not body:raise ValueError('Empty NBA registry response')
        return body,{'http_status':response.status,'content_type':response.headers.get('Content-Type',''),'final_url':final}

def run(root,timeout=20,fixture=None,reconcile=False):
    root=root.resolve();base=root/'research/p0_s8/s8_22_10_21/results'/SEASON
    fetched_at=dt.datetime.now(dt.timezone.utc).isoformat()
    if fixture:
        body=fixture.resolve().read_bytes();transport={'http_status':None,'content_type':'application/json','final_url':None}
        mode='OFFLINE_FIXTURE_UNVERIFIED'
    else:
        body,transport=fetch(timeout);mode='LIVE_NBA_STATS_RESPONSE'
    count,unique=validate(body)
    digest=sha(body);out=base/digest[:16];out.mkdir(parents=True,exist_ok=True)
    rawfile=out/'commonallplayers_raw.json'
    if rawfile.exists() and rawfile.read_bytes()!=body:raise ValueError('Output collision; refusing overwrite')
    rawfile.write_bytes(body)
    manifest={'milestone':'S8.22.10.21','source':'NBA Stats CommonAllPlayers','season_parameter':SEASON,
              'requested_url':url(),'retrieved_at_utc':fetched_at,'mode':mode,'raw_sha256':digest,
              'raw_bytes':len(body),'registry_rows':count,'unique_person_ids':unique,
              'transport':transport,'fixture_source_path':str(fixture.resolve()) if fixture else None,
              'historical_team_membership_certified':False,'player_identity_certified':False,
              'injury_status_certified':False,'historical_asof_certified':False,
              'research_status':'RESEARCH_ONLY','training_decision':'BLOCK_TRAINING',
              'caveat':'NBA season parameter does not certify team membership on the target date; retrieval time is not historical report publication time.'}
    (out/'capture_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('CAPTURE:',rawfile);print('MANIFEST:',out/'capture_manifest.json');print(json.dumps(manifest,indent=2))
    if reconcile:
        cmd=[sys.executable,str(root/'research/p0_s8/s8_22_10_20/run_s8_22_10_20.py'),'--project-root',str(root),'--registry-json',str(rawfile)]
        print('RUNNING EXISTING RECONCILIATION:', ' '.join(cmd),flush=True)
        cp=subprocess.run(cmd,check=False)
        if cp.returncode:raise ValueError('S8.22.10.20 reconciliation failed with code '+str(cp.returncode))
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project-root',type=Path,default=Path('.'))
    p.add_argument('--timeout',type=int,default=20);p.add_argument('--offline-fixture',type=Path)
    p.add_argument('--reconcile',action='store_true');a=p.parse_args()
    try:
        if not 1<=a.timeout<=60:raise ValueError('Timeout must be 1–60 seconds')
        run(a.project_root,a.timeout,a.offline_fixture,a.reconcile)
    except (ValueError,FileNotFoundError,UnicodeError,urllib.error.URLError,TimeoutError,json.JSONDecodeError) as exc:
        p.exit(2,'FAIL CLOSED: '+str(exc)+'\n')
