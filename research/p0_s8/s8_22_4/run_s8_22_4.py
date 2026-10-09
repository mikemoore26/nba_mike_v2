"""S8.22.4 manually invoked BALLDONTLIE NBA games adapter; fail-closed research only."""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ENDPOINT = 'https://api.balldontlie.io/v1/games'
MAX_BYTES = 3_000_000


def load_s821(project_root: Path):
    path = project_root/'research/p0_s8/s8_21/run_s8_21.py'
    if not path.is_file():
        raise FileNotFoundError(f'S8.21 dependency missing: {path}')
    spec = importlib.util.spec_from_file_location('s821_capture_for_s8224', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_key(root: Path):
    # Avoid dotenv.find_dotenv() stdin-stack AssertionError; never display key.
    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise RuntimeError('Install python-dotenv: python -m pip install python-dotenv') from exc
    load_dotenv(dotenv_path=root/'.env', override=False)
    key = os.getenv('BALLDONTLIE_API_KEY', '').strip()
    if not key:
        raise RuntimeError('BALLDONTLIE_API_KEY missing; add it to local .env (do not share)')
    if '\r' in key or '\n' in key:
        raise RuntimeError('Invalid API key formatting')
    return key


def fetch(key: str, game_date: str, opener=urlopen):
    url = ENDPOINT+'?'+urlencode({'dates[]':game_date,'per_page':100})
    req = Request(url, headers={'Authorization':key,'Accept':'application/json','User-Agent':'NBA-MIKE-v2-research/0.1'},method='GET')
    try:
        with opener(req,timeout=15) as response:
            status = response.getcode()
            body = response.read(MAX_BYTES+1)
            if len(body)>MAX_BYTES:
                return None, status, 'BODY_TOO_LARGE', url, {}
            headers = {k.lower():v for k,v in response.headers.items() if k.lower() in ('content-type','date','x-ratelimit-remaining','retry-after')}
            if status!=200:
                return None,status,f'HTTP_{status}',url,headers
            return body,status,None,url,headers
    except HTTPError as exc:
        # Never store error bodies; they can echo request data.
        return None,exc.code,f'HTTP_{exc.code}',url,{}
    except (URLError, TimeoutError, OSError) as exc:
        return None,None,'NETWORK_'+type(exc).__name__,url,{}


def parse_games(body: bytes, requested_date: str):
    try:
        obj=json.loads(body)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError('INVALID_JSON') from exc
    if not isinstance(obj,dict) or not isinstance(obj.get('data'),list) or not isinstance(obj.get('meta'),dict):
        raise ValueError('INVALID_ENVELOPE')
    meta=obj['meta']
    if meta.get('next_cursor') not in (None,'',0):
        raise ValueError('PAGINATION_INCOMPLETE')
    games=[]; seen=set()
    for g in obj['data']:
        if not isinstance(g,dict): raise ValueError('INVALID_GAME')
        gid=g.get('id'); dt=g.get('datetime'); day=g.get('date')
        home=g.get('home_team'); away=g.get('visitor_team')
        if not isinstance(gid,int) or isinstance(gid,bool) or gid<=0 or gid in seen:
            raise ValueError('INVALID_OR_DUPLICATE_GAME_ID')
        seen.add(gid)
        if not isinstance(home,dict) or not isinstance(away,dict): raise ValueError('MISSING_TEAM')
        hid=home.get('id'); aid=away.get('id')
        if not all(isinstance(x,int) and not isinstance(x,bool) and x>0 for x in (hid,aid)) or hid==aid:
            raise ValueError('INVALID_TEAMS')
        if not isinstance(day,str) or day[:10]!=requested_date:
            raise ValueError('DATE_MISMATCH')
        # Some provider records lack a tipoff time; do not invent midnight tipoffs.
        tipoff=''; tipoff_status='MISSING'
        if isinstance(dt,str) and ('T' in dt) and (dt.endswith('Z') or '+' in dt[10:] or '-' in dt[10:]):
            try:
                t=datetime.fromisoformat(dt.replace('Z','+00:00'))
                if t.tzinfo is None: raise ValueError()
                tipoff=t.astimezone(timezone.utc).isoformat()
                tipoff_status='PRESENT_UNVERIFIED'
            except ValueError as exc:
                raise ValueError('INVALID_TIPOFF') from exc
        games.append({'provider':'balldontlie','provider_game_id':gid,'official_nba_game_id':'',
                      'game_date':requested_date,'home_provider_team_id':hid,'away_provider_team_id':aid,
                      'tipoff_utc':tipoff,'tipoff_status':tipoff_status,
                      'game_status':str(g.get('status',''))[:100]})
    return games


def run(root: Path, *, game_date: str, checkpoint: str='T-24H', live: bool=False, fixture: Path|None=None, opener=urlopen):
    root=Path(root).resolve()
    try:
        if date.fromisoformat(game_date).isoformat()!=game_date: raise ValueError()
    except ValueError as exc:
        raise ValueError('date must be YYYY-MM-DD') from exc
    if live == (fixture is not None):
        raise ValueError('Choose exactly one of --live or --fixture')
    s821=load_s821(root)
    if checkpoint not in s821.CHECKPOINTS: raise ValueError('Invalid checkpoint')
    if live:
        key=load_key(root)
        body,status,error,url,headers=fetch(key,game_date,opener=opener)
        mode='LIVE_MANUAL'
    else:
        body=Path(fixture).read_bytes()
        if len(body)>MAX_BYTES: raise ValueError('Fixture exceeds 3MB')
        status=200;error=None;url='fixture://balldontlie/games';headers={};mode='OFFLINE_FIXTURE'
    storage=root/'research/p0_s8/s8_21/artifacts'
    event=s821.capture(storage,kind='schedule',url=url,checkpoint=checkpoint,
                       payload=body,game_id='',http_status=status,error_code=error)
    games=[]; parse_status='NOT_ATTEMPTED' if error else 'PASS'
    if not error:
        try: games=parse_games(body,game_date)
        except ValueError as exc: parse_status=str(exc);games=[]
    results=root/'research/p0_s8/s8_22_4/results';results.mkdir(parents=True,exist_ok=True)
    fields=['provider','provider_game_id','official_nba_game_id','game_date','home_provider_team_id',
            'away_provider_team_id','tipoff_utc','tipoff_status','game_status']
    with (results/'s8_22_4_games.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(games)
    report={'milestone':'S8.22.4','mode':mode,'requested_date':game_date,'checkpoint':checkpoint,
            'source_url':url,'http_status':status,'retrieval_error':error,
            'capture_outcome':event['outcome'],'capture_event_id':event['event_id'],
            'raw_sha256':event['sha256'],'response_headers_allowlisted':headers,
            'parse_status':parse_status,'parsed_games':len(games),
            'game_id_mapping':'UNVERIFIED','tipoff_accuracy':'UNVERIFIED',
            'provider_entitlement':'NOT_INDEPENDENTLY_VERIFIED',
            'source_approval':'PENDING_TERMS_AND_VALIDATION',
            'pregame_player_eligibility_verified':False,'training_eligible':False,
            'status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING',
            'limitations':['Manual single-page request only','No automated retries or scheduling',
                           'Parsed rows are provider IDs, not official NBA IDs',
                           'Capture receipt time does not certify eligibility or game completeness']}
    (results/'s8_22_4_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',type=Path,default=Path('.'))
    p.add_argument('--date',required=True)
    p.add_argument('--checkpoint',default='T-24H')
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--live',action='store_true');g.add_argument('--fixture',type=Path)
    a=p.parse_args()
    result=run(a.project_root,game_date=a.date,checkpoint=a.checkpoint,live=a.live,fixture=a.fixture)
    print(json.dumps({k:result[k] for k in ('mode','http_status','retrieval_error','capture_outcome','parse_status','parsed_games','decision')},indent=2))
    if result['retrieval_error'] or result['parse_status']!='PASS': raise SystemExit(2)

if __name__=='__main__': main()
