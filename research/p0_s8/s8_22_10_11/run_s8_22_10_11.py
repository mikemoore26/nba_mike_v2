"""S8.22.10.11 independent schedule-page discovery, immutable evidence, fail-closed reconciliation."""
import argparse
import csv
import datetime as dt
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.error
import urllib.request
from collections import Counter

DATE='2023-11-15'
SCHEDULE_URL='https://www.nba.com/games?date=2023-11-15'
GAME_RE=re.compile(r'(?:https?://(?:www\.)?nba\.com)?/game/([a-z]{2,3})-(?:vs|at)-([a-z]{2,3})-(002\d{7})(?=[^\w]|$)',re.I)
FIELDS=['game_date','away_at_home','provisional_nba_game_id','discovered_nba_game_id','discovery_status','page_title_status','schedule_snapshot_sha256','game_page_snapshot_sha256','evidence_status','review_decision','reviewer','reviewed_at_utc']
def sha(data): return hashlib.sha256(data).hexdigest()
def load_csv(path):
 with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write_csv(path,rows):
 with path.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
class Links(HTMLParser):
 def __init__(self):super().__init__();self.hrefs=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a':
   href=dict(attrs).get('href')
   if href:self.hrefs.append(href)
def discover(html):
 """Use ONLY actual anchor hrefs, not embedded scripts, navigation text, or provisional IDs."""
 parser=Links();parser.feed(html.decode('utf-8'))
 found={};conflicts=set()
 for href in parser.hrefs:
  m=GAME_RE.search(href)
  if not m:continue
  away,home,gid=m.group(1).upper(),m.group(2).upper(),m.group(3)
  key=f'{away}@{home}'
  if key in conflicts:continue
  if key in found and found[key]!=gid:conflicts.add(key)
  else:found[key]=gid
 for key in conflicts:found.pop(key,None)
 return found,conflicts

def fetch(url,timeout):
 req=urllib.request.Request(url,headers={'User-Agent':'NBA-MIKE-v2-research-evidence/1.0','Accept':'text/html'})
 with urllib.request.urlopen(req,timeout=timeout) as resp:
  if resp.status!=200:raise RuntimeError(f'HTTP {resp.status}')
  data=resp.read(6_000_001)
  if len(data)>6_000_000:raise RuntimeError('Response exceeds 6 MB')
  return data

def snapshot(path,url,timeout,offline,fetcher=fetch):
 """Existing immutable snapshots always reused; never replace evidence."""
 receipt=path.with_suffix('.receipt.json')
 if path.exists():
  data=path.read_bytes();status='REUSED_EXISTING_SNAPSHOT'
 elif offline:return None,'OFFLINE_NO_SNAPSHOT',''
 else:
  try:data=fetcher(url,timeout)
  except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,OSError,RuntimeError) as e:return None,'FETCH_FAILED',f'{type(e).__name__}: {str(e)[:180]}'
  path.parent.mkdir(parents=True,exist_ok=True)
  with path.open('xb') as f:f.write(data)
  status='DOWNLOADED'
 digest=sha(data)
 if receipt.exists():
  old=json.loads(receipt.read_text(encoding='utf-8'))
  if old['sha256']!=digest or old['source_url']!=url:raise ValueError('Evidence receipt mismatch: '+str(path))
 else:
  receipt.write_text(json.dumps({'source_url':url,'sha256':digest,'bytes':len(data),'captured_at_utc':dt.datetime.now(dt.timezone.utc).isoformat() if status=='DOWNLOADED' else None,'historical_asof':'NOT_CERTIFIED'},indent=2)+'\n',encoding='utf-8')
 return data,status,''

def reconcile(crosswalk,discovered,conflicts,page_rows,schedule_digest):
 targets=[r for r in crosswalk if r.get('game_date')==DATE and r.get('game_id_status')=='UNVERIFIED_PROVISIONAL']
 if len(targets)!=8 or len({r['away_at_home'] for r in targets})!=8:raise ValueError('Expected 8 unique target matchups')
 page_index={r['away_at_home']:r for r in page_rows}
 if len(page_index)!=len(page_rows):raise ValueError('Duplicate game page rows')
 out=[]
 for r in sorted(targets,key=lambda r:r['away_at_home']):
  key=r['away_at_home'];old=r['provisional_nba_game_id'];new=discovered.get(key,'')
  status='CONFLICTING_SCHEDULE_LINKS' if key in conflicts else 'NOT_DISCOVERED' if not new else 'ID_MISMATCH' if new!=old else 'ID_MATCH'
  page=page_index.get(key,{})
  title=page.get('content_status','MISSING_PAGE_EVIDENCE')
  # schedule link ID is independent of URL built from provisional ID, but no certification yet
  evidence='CANDIDATE_REVIEW_REQUIRED' if status=='ID_MATCH' and title=='TITLE_MATCH_REVIEW_REQUIRED' and page.get('snapshot_sha256') else 'BLOCKED'
  out.append(dict(game_date=DATE,away_at_home=key,provisional_nba_game_id=old,discovered_nba_game_id=new,discovery_status=status,page_title_status=title,schedule_snapshot_sha256=schedule_digest,game_page_snapshot_sha256=page.get('snapshot_sha256',''),evidence_status=evidence,review_decision='PENDING',reviewer='',reviewed_at_utc=''))
 return out

def main():
 p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');p.add_argument('--crosswalk');p.add_argument('--page-evidence');p.add_argument('--schedule-html',help='Locally supplied independently acquired schedule HTML; archived immutably');p.add_argument('--offline',action='store_true');p.add_argument('--timeout',type=float,default=20);a=p.parse_args()
 root=Path(a.project_root).resolve()
 cw=Path(a.crosswalk).resolve() if a.crosswalk else next(iter((root/'research/p0_s8/s8_22_10_7/results'/DATE).glob('*/provisional_game_id_crosswalk.csv')),None)
 pages=Path(a.page_evidence).resolve() if a.page_evidence else next(iter((root/'research/p0_s8/s8_22_10_10/results'/DATE).glob('*/game_page_evidence.csv')),None)
 if not cw or not cw.is_file() or not pages or not pages.is_file():raise FileNotFoundError('Crosswalk/page evidence missing; pass --crosswalk and --page-evidence')
 token=sha(cw.read_bytes())[:16]
 archive=root/'research/p0_s8/s8_22_10_11/evidence'/DATE
 path=archive/'nba_schedule_2023-11-15.html'
 if a.schedule_html and not path.exists():
  supplied=Path(a.schedule_html).resolve().read_bytes();archive.mkdir(parents=True,exist_ok=True)
  with path.open('xb') as f:f.write(supplied)
 # A local input is a user-provided schedule capture, not independently authenticated by this script.
 data,acquisition,error=snapshot(path,SCHEDULE_URL,a.timeout,a.offline)
 found,conflicts=discover(data) if data else ({},set())
 rows=reconcile(load_csv(cw),found,conflicts,load_csv(pages),sha(data) if data else '')
 out=root/'research/p0_s8/s8_22_10_11/results'/DATE/token;out.mkdir(parents=True,exist_ok=True)
 write_csv(out/'independent_schedule_reconciliation.csv',rows)
 report={'milestone':'S8.22.10.11','source_url':SCHEDULE_URL,'schedule_acquisition':acquisition,'schedule_error':error,'schedule_sha256':sha(data) if data else None,'discovered_link_count':len(found),'conflicting_link_matchups':sorted(conflicts),'target_games':len(rows),'discovery_counts':dict(Counter(r['discovery_status'] for r in rows)),'evidence_counts':dict(Counter(r['evidence_status'] for r in rows)),'independently_certified_game_ids':0,'manual_player_reviews_completed':0,'historical_asof':'NOT_CERTIFIED','decision':'BLOCK_TRAINING','note':'Schedule anchor links are discovered without using provisional IDs. HTML may omit server-rendered links; failure is not evidence of an incorrect ID. Independently supplied HTML requires provenance review. No automatic certification.'}
 (out/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print('REPORT:',out/'review.json');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
