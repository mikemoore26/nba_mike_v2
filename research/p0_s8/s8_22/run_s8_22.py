"""S8.22 manually triggered NBA schedule acquisition. No scheduling or training.

Official-looking host is an allowlisted candidate, not a guarantee of rights,
availability, schema stability, or independently verified pregame evidence.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import ssl
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

URL = 'https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json'
MAX_BYTES = 3_000_000
CHECKPOINTS = ('T-24H','T-6H','T-90M','T-30M')
GAME_ID = re.compile(r'^\d{10}$')
TEAM = re.compile(r'^[A-Z]{3}$')


def load_s821(project_root: Path):
    path=project_root/'research/p0_s8/s8_21/run_s8_21.py'
    if not path.is_file():
        raise FileNotFoundError(f'S8.21 dependency missing: {path}')
    spec=importlib.util.spec_from_file_location('nba_s821_capture',path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_schedule(payload: bytes):
    """Fail closed on schema drift; return normalized schedule rows."""
    try:
        obj=json.loads(payload)
    except (ValueError,UnicodeDecodeError) as exc:
        raise ValueError('INVALID_JSON') from exc
    if not isinstance(obj,dict) or not isinstance(obj.get('leagueSchedule'),dict):
        raise ValueError('MISSING_LEAGUE_SCHEDULE')
    dates=obj['leagueSchedule'].get('gameDates')
    if not isinstance(dates,list) or not dates:
        raise ValueError('MISSING_GAME_DATES')
    rows=[]; seen=set()
    for date in dates:
        if not isinstance(date,dict) or not isinstance(date.get('games'),list):
            raise ValueError('INVALID_DATE_GAMES')
        for game in date['games']:
            if not isinstance(game,dict): raise ValueError('INVALID_GAME')
            gid=game.get('gameId')
            if not isinstance(gid,str) or not GAME_ID.fullmatch(gid):
                raise ValueError('INVALID_GAME_ID')
            if gid in seen: raise ValueError('DUPLICATE_GAME_ID')
            seen.add(gid)
            tip=game.get('gameDateTimeUTC')
            if not isinstance(tip,str): raise ValueError('MISSING_TIPOFF_UTC')
            try:
                parsed=datetime.fromisoformat(tip.replace('Z','+00:00'))
            except ValueError as exc:
                raise ValueError('INVALID_TIPOFF_UTC') from exc
            if parsed.tzinfo is None or parsed.utcoffset().total_seconds()!=0:
                raise ValueError('NON_UTC_TIPOFF')
            home=game.get('homeTeam');away=game.get('awayTeam')
            if not isinstance(home,dict) or not isinstance(away,dict):
                raise ValueError('MISSING_TEAMS')
            h=home.get('teamTricode');a=away.get('teamTricode')
            if not isinstance(h,str) or not TEAM.fullmatch(h) or not isinstance(a,str) or not TEAM.fullmatch(a) or h==a:
                raise ValueError('INVALID_TEAM_TRICODE')
            rows.append({'game_id':gid,'tipoff_utc':parsed.astimezone(timezone.utc).isoformat(),
                         'home_team':h,'away_team':a,'game_status':str(game.get('gameStatus',''))})
    if not rows: raise ValueError('EMPTY_GAMES')
    return sorted(rows,key=lambda r:(r['tipoff_utc'],r['game_id']))


def fetch_live(url: str = URL):
    if url != URL: raise ValueError('UNAPPROVED_SOURCE_URL')
    req=Request(url,headers={'User-Agent':'NBA_MIKE_v2_research_capture/0.1','Accept':'application/json'})
    with urlopen(req,timeout=15,context=ssl.create_default_context()) as response:
        status=response.status
        headers={k.lower():v for k,v in response.headers.items() if k.lower() in ('date','content-type','etag','last-modified','content-length','cache-control')}
        body=response.read(MAX_BYTES+1)
        if len(body)>MAX_BYTES: raise ValueError('RESPONSE_TOO_LARGE')
        return status,headers,body


def write_json(path:Path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')


def run(project_root:Path, *, live=False, fixture:Path|None=None, checkpoint='T-24H', fetcher=fetch_live):
    if checkpoint not in CHECKPOINTS: raise ValueError('INVALID_CHECKPOINT')
    if live == (fixture is not None):
        raise ValueError('Specify exactly one of --live or --fixture')
    s821=load_s821(project_root)
    base=project_root/'research/p0_s8/s8_22'
    resultdir=base/'results'
    resultdir.mkdir(parents=True,exist_ok=True)
    ledgerroot=project_root/'research/p0_s8/s8_21/artifacts'
    headers={}; status=None; payload=None; error=None
    if live:
        try:
            status,headers,payload=fetcher(URL)
            if status!=200:
                error=f'HTTP_{status}'
                payload=None
        except (HTTPError,URLError,TimeoutError,OSError,ValueError) as exc:
            error='RETRIEVAL_FAILED_'+type(exc).__name__
    else:
        try:
            payload=Path(fixture).read_bytes()
            if len(payload)>MAX_BYTES:
                payload=None;error='FIXTURE_TOO_LARGE'
            else:
                status=200
        except OSError as exc:
            error='FIXTURE_READ_FAILED_'+type(exc).__name__
    received=datetime.now(timezone.utc).isoformat()
    source_url=URL if live else 'fixture://nba/schedule'
    # S8.21 captures bytes even if later parsing fails; retrieval errors get a failure ledger event.
    event=s821.capture(ledgerroot,kind='schedule',url=source_url,checkpoint=checkpoint,
                       payload=payload,http_status=status,error_code=error,game_id='SCHEDULE_FEED')
    rows=[]; parse_status='NOT_ATTEMPTED'
    if payload is not None:
        try:
            rows=parse_schedule(payload)
            parse_status='PASS'
        except ValueError as exc:
            parse_status=str(exc)
    # Per-attempt receipt/HTTP metadata. Publisher timestamps are not as-of proof.
    metadata={'milestone':'S8.22','event_id':event['event_id'],'source_url':source_url,
              'mode':'LIVE_MANUAL' if live else 'OFFLINE_FIXTURE','requested_checkpoint':checkpoint,
              'request_finished_utc':received,'s821_received_utc_is_authoritative':True,
              'http_status':status,'response_headers':headers,'sha256':event['sha256'],
              'capture_outcome':event['outcome'],'retrieval_error':error,
              'parse_status':parse_status,'parsed_game_count':len(rows),
              'historical_asof_certified':False,'pregame_player_eligibility_verified':False,
              'decision':'BLOCK_TRAINING','status':'RESEARCH_ONLY'}
    write_json(resultdir/f's8_22_receipt_{event["event_id"]}.json',metadata)
    write_json(resultdir/'s8_22_report.json',metadata)
    with (resultdir/'s8_22_games.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['game_id','tipoff_utc','home_team','away_team','game_status'])
        writer.writeheader();writer.writerows(rows)
    return metadata


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',type=Path,default=Path('.'))
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--fixture',type=Path)
    group.add_argument('--live',action='store_true',help='Explicit opt-in: one network request to allowlisted NBA CDN URL')
    parser.add_argument('--checkpoint',choices=CHECKPOINTS,default='T-24H')
    args=parser.parse_args()
    report=run(args.project_root.resolve(),live=args.live,fixture=args.fixture,checkpoint=args.checkpoint)
    print(json.dumps(report,indent=2))
    if report['parse_status']!='PASS': sys.exit(2)

if __name__=='__main__': main()
