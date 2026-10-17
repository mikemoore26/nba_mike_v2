"""S8.22.10.9: archive NBA CDN game boxscores, verify contents without promotion."""
import argparse,csv,hashlib,json,re,urllib.request,urllib.error,datetime
from pathlib import Path
from collections import Counter

TEAM_IDS={'ATL':1610612737,'BOS':1610612738,'BKN':1610612751,'CHA':1610612766,'CHI':1610612741,'CLE':1610612739,'DAL':1610612742,'DEN':1610612743,'DET':1610612765,'GSW':1610612744,'HOU':1610612745,'IND':1610612754,'LAC':1610612746,'LAL':1610612747,'MEM':1610612763,'MIA':1610612748,'MIL':1610612749,'MIN':1610612750,'NOP':1610612740,'NYK':1610612752,'OKC':1610612760,'ORL':1610612753,'PHI':1610612755,'PHX':1610612756,'POR':1610612757,'SAC':1610612758,'SAS':1610612759,'TOR':1610612761,'UTA':1610612762,'WAS':1610612764}
FIELDS=['game_date','away_at_home','provisional_nba_game_id','source_url','snapshot_path','snapshot_sha256','source_row_reference','reviewer','reviewed_at_utc','review_decision','acquisition_status','content_status','content_detail']

def sha(b):return hashlib.sha256(b).hexdigest()
def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write_csv(p,rs,fields):
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rs)
def inspect(payload,expected_id,date,matchup):
 try: doc=json.loads(payload)
 except (ValueError,UnicodeDecodeError):return 'INVALID_JSON','Response not valid JSON'
 game=doc.get('game') if isinstance(doc,dict) else None
 if not isinstance(game,dict):return 'INVALID_SCHEMA','Missing game object'
 gid=str(game.get('gameId',''))
 if gid!=expected_id:return 'GAME_ID_MISMATCH',f'expected {expected_id}; source {gid}'
 away,home=matchup.split('@')
 a=game.get('awayTeam') or {};h=game.get('homeTeam') or {}
 try: aid=int(a.get('teamId'));hid=int(h.get('teamId'))
 except (TypeError,ValueError):return 'MISSING_TEAM_IDS','Cannot extract home/away team IDs'
 if (aid,hid)!=(TEAM_IDS[away],TEAM_IDS[home]):return 'TEAM_MISMATCH',f'expected {TEAM_IDS[away]}@{TEAM_IDS[home]}; source {aid}@{hid}'
 # gameTimeUTC and gameTimeLocal may straddle calendar days; prefer source gameDate if present.
 source_date=game.get('gameDate')
 if not source_date:
  source_date=game.get('gameTimeLocal')
 if not source_date:return 'DATE_NOT_CHECKED','No unambiguous source game date; game ID and team IDs match'
 source_date=str(source_date)[:10]
 if source_date!=date:return 'DATE_MISMATCH',f'expected {date}; source {source_date}'
 return 'CONTENT_MATCH','NBA CDN gameId, home/away team IDs and source local game date match'
def acquire(url,timeout):
 req=urllib.request.Request(url,headers={'User-Agent':'NBA-MIKE-v2-research-evidence/1.0','Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=timeout) as resp:
  if resp.status!=200:raise RuntimeError(f'HTTP {resp.status}')
  data=resp.read(4_000_001)
  if len(data)>4_000_000:raise RuntimeError('Response too large')
  return data

def process(crosswalk,archive,fetch,timeout):
 targets=[r for r in crosswalk if r.get('game_id_status')=='UNVERIFIED_PROVISIONAL']
 if len(targets)!=8:raise ValueError('Expected exactly eight provisional target games')
 if len({(r['game_date'],r['away_at_home']) for r in targets})!=8:raise ValueError('Duplicate game key')
 if len({r['provisional_nba_game_id'] for r in targets})!=8:raise ValueError('Duplicate game ID')
 results=[]
 for r in sorted(targets,key=lambda x:x['provisional_nba_game_id']):
  date=r['game_date'];match=r['away_at_home'];gid=r['provisional_nba_game_id']
  if not re.fullmatch(r'002\d{7}',gid):raise ValueError('Unexpected NBA regular-season game ID: '+gid)
  url=f'https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{gid}.json'
  folder=archive/gid;folder.mkdir(parents=True,exist_ok=True)
  path=folder/'nba_cdn_boxscore.json';receipt=folder/'receipt.json'
  row={'game_date':date,'away_at_home':match,'provisional_nba_game_id':gid,'source_url':url,'snapshot_path':'','snapshot_sha256':'','source_row_reference':'game.gameId;game.homeTeam.teamId;game.awayTeam.teamId;game.gameDate or game.gameTimeLocal','reviewer':'','reviewed_at_utc':'','review_decision':'PENDING','acquisition_status':'NOT_ATTEMPTED','content_status':'NOT_CHECKED','content_detail':''}
  if path.exists():
   data=path.read_bytes();row['acquisition_status']='REUSED_EXISTING_SNAPSHOT'
  elif fetch:
   try:
    data=acquire(url,timeout)
    # Never overwrite an existing snapshot.
    with path.open('xb') as f:f.write(data)
    row['acquisition_status']='DOWNLOADED'
   except (urllib.error.URLError,TimeoutError,OSError,RuntimeError) as exc:
    row['acquisition_status']='FETCH_FAILED';row['content_detail']=f'{type(exc).__name__}: {str(exc)[:180]}'
    data=None
  else:data=None
  if data is not None:
   digest=sha(data);row['snapshot_path']=str(path.resolve());row['snapshot_sha256']=digest
   row['content_status'],row['content_detail']=inspect(data,gid,date,match)
   new_receipt={'source_url':url,'sha256':digest,'bytes':len(data),'acquired_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat() if row['acquisition_status']=='DOWNLOADED' else None,'game_id':gid,'content_status':row['content_status'],'historical_asof':'NOT_CERTIFIED'}
   if not receipt.exists():
    with receipt.open('x',encoding='utf-8') as f:json.dump(new_receipt,f,indent=2);f.write('\n')
   else:
    old=json.loads(receipt.read_text(encoding='utf-8'))
    if old.get('sha256')!=digest:raise ValueError('Existing receipt hash differs from snapshot for '+gid)
  results.append(row)
 return results

def main():
 p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');p.add_argument('--crosswalk');p.add_argument('--archive');p.add_argument('--output');p.add_argument('--timeout',type=float,default=15);p.add_argument('--offline',action='store_true');a=p.parse_args()
 root=Path(a.project_root).resolve()
 if a.crosswalk:cw=Path(a.crosswalk).resolve()
 else:
  candidates=list((root/'research/p0_s8/s8_22_10_7/results/2023-11-15').glob('*/provisional_game_id_crosswalk.csv'))
  if len(candidates)!=1:raise RuntimeError('Expected one crosswalk; use --crosswalk')
  cw=candidates[0]
 archive=Path(a.archive).resolve() if a.archive else root/'research/p0_s8/s8_22_10_9/evidence/2023-11-15'
 rows=process(read_csv(cw),archive,not a.offline,a.timeout)
 token=sha(cw.read_bytes())[:16];out=Path(a.output).resolve() if a.output else root/'research/p0_s8/s8_22_10_9/results/2023-11-15'/token
 out.mkdir(parents=True,exist_ok=True);write_csv(out/'game_id_source_evidence.csv',rows,FIELDS)
 report={'milestone':'S8.22.10.9','crosswalk_sha256':sha(cw.read_bytes()),'target_games':len(rows),'acquisition_counts':dict(Counter(r['acquisition_status'] for r in rows)),'content_counts':dict(Counter(r['content_status'] for r in rows)),'content_matches_requiring_independent_review':sum(r['content_status']=='CONTENT_MATCH' for r in rows),'verified_game_ids':0,'historical_asof':'NOT_CERTIFIED','player_identity':'NOT_CERTIFIED','manual_reviews_completed':0,'decision':'BLOCK_TRAINING','note':'Contemporaneously downloaded historical boxscores prove current source contents, not historical publication timing. Matching CDN JSON requires independent review; no automatic certification.'}
 (out/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print('REPORT:',out/'review.json');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
