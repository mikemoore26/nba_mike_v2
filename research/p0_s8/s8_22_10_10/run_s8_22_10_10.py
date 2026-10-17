"""S8.22.10.10: preserve NBA public game-page evidence; never certify as-of/training."""
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

NAMES = {'ATL':'Atlanta Hawks','BOS':'Boston Celtics','CLE':'Cleveland Cavaliers','CHI':'Chicago Bulls','DAL':'Dallas Mavericks','LAL':'Los Angeles Lakers','MIL':'Milwaukee Bucks','MIN':'Minnesota Timberwolves','NYK':'New York Knicks','ORL':'Orlando Magic','PHI':'Philadelphia 76ers','PHX':'Phoenix Suns','POR':'Portland Trail Blazers','SAC':'Sacramento Kings','TOR':'Toronto Raptors','WAS':'Washington Wizards'}
FIELDS=['game_date','away_at_home','provisional_nba_game_id','source_url','snapshot_path','snapshot_sha256','http_status','acquisition_status','content_status','content_detail','reviewer','reviewed_at_utc','review_decision']
def sha(b): return hashlib.sha256(b).hexdigest()
def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f: return list(csv.DictReader(f))
def write_csv(p,rows):
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
class Page(HTMLParser):
 def __init__(self): super().__init__();self.title='';self.meta=[];self.in_title=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='title':self.in_title=True
  if tag=='meta' and a.get('property') in ('og:title','twitter:title') and a.get('content'):self.meta.append(a['content'])
 def handle_endtag(self,tag):
  if tag=='title':self.in_title=False
 def handle_data(self,data):
  if self.in_title:self.title+=data

def inspect(html,game_date,matchup,gid):
 try: page=Page();page.feed(html.decode('utf-8'))
 except (UnicodeDecodeError,ValueError) as e:return 'INVALID_HTML',type(e).__name__
 titles=[page.title]+page.meta
 if not any(t.strip() for t in titles):return 'MISSING_TITLE','No HTML title or social title'
 away,home=matchup.split('@')
 # Strictly use page titles, not arbitrary body mentions or page embedded navigation.
 def matches(t):
  norm=re.sub(r'[^a-z0-9]+',' ',t.lower())
  return all(re.sub(r'[^a-z0-9]+',' ',NAMES[x].lower()) in norm for x in (away,home))
 if not any(matches(t) for t in titles):return 'TEAM_TITLE_MISMATCH','Full team names absent from a single page title'
 d=dt.date.fromisoformat(game_date)
 date_pattern=rf'\b{d.strftime("%b")}\w*\s+0?{d.day},?\s+{d.year}\b'
 if not any(re.search(date_pattern,t,re.I) for t in titles):return 'DATE_TITLE_NOT_CONFIRMED','Local game date absent from page title'
 # ID appears in requested URL, not necessarily independently asserted in page content.
 return 'TITLE_MATCH_REVIEW_REQUIRED','Page title names both teams and local game date; game ID is URL-only; human corroboration required'

def acquire(url,timeout):
 req=urllib.request.Request(url,headers={'User-Agent':'NBA-MIKE-v2-evidence/1.0','Accept':'text/html'})
 with urllib.request.urlopen(req,timeout=timeout) as resp:
  code=resp.status
  if code!=200:raise RuntimeError('HTTP '+str(code))
  data=resp.read(5_000_001)
  if len(data)>5_000_000:raise RuntimeError('Response over 5 MB')
  return code,data

def process(crosswalk,archive,fetch,timeout,fetcher=acquire):
 targets=[r for r in crosswalk if r.get('game_id_status')=='UNVERIFIED_PROVISIONAL']
 if len(targets)!=8 or len({(r['game_date'],r['away_at_home']) for r in targets})!=8:raise ValueError('Expected eight unique provisional games')
 if len({r['provisional_nba_game_id'] for r in targets})!=8:raise ValueError('Duplicate game ID')
 results=[]
 for r in sorted(targets,key=lambda x:x['away_at_home']):
  day,match,gid=r['game_date'],r['away_at_home'],r['provisional_nba_game_id']
  if not re.fullmatch(r'002\d{7}',gid) or not re.fullmatch(r'[A-Z]{3}@[A-Z]{3}',match):raise ValueError('Bad crosswalk fields')
  away,home=match.split('@')
  if away not in NAMES or home not in NAMES:raise ValueError('Unknown team')
  url=f'https://www.nba.com/game/{away.lower()}-vs-{home.lower()}-{gid}'
  folder=archive/gid;folder.mkdir(parents=True,exist_ok=True)
  path=folder/'nba_game_page.html';receipt=folder/'receipt.json'
  row=dict(game_date=day,away_at_home=match,provisional_nba_game_id=gid,source_url=url,snapshot_path='',snapshot_sha256='',http_status='',acquisition_status='NOT_ATTEMPTED',content_status='NOT_CHECKED',content_detail='',reviewer='',reviewed_at_utc='',review_decision='PENDING')
  data=None
  if path.exists():data=path.read_bytes();row['acquisition_status']='REUSED_EXISTING_SNAPSHOT'
  elif fetch:
   try:
    code,data=fetcher(url,timeout);row['http_status']=str(code)
    with path.open('xb') as f:f.write(data)
    row['acquisition_status']='DOWNLOADED'
   except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,OSError,RuntimeError) as exc:
    row['acquisition_status']='FETCH_FAILED';row['http_status']=str(getattr(exc,'code',''))
    row['content_detail']=f'{type(exc).__name__}: {str(exc)[:160]}'
  if data is not None:
   digest=sha(data);row['snapshot_path']=str(path.resolve());row['snapshot_sha256']=digest
   row['content_status'],row['content_detail']=inspect(data,day,match,gid)
   if receipt.exists():
    old=json.loads(receipt.read_text(encoding='utf-8'))
    if old.get('sha256')!=digest:raise ValueError('Receipt hash mismatch for '+gid)
   else:
    obj={'source_url':url,'sha256':digest,'bytes':len(data),'acquired_at_utc':dt.datetime.now(dt.timezone.utc).isoformat() if row['acquisition_status']=='DOWNLOADED' else None,'status':row['content_status'],'historical_asof':'NOT_CERTIFIED','source_type':'PUBLIC_GAME_PAGE_HTML'}
    with receipt.open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2);f.write('\n')
  results.append(row)
 return results

def main():
 p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');p.add_argument('--crosswalk');p.add_argument('--archive');p.add_argument('--output');p.add_argument('--timeout',type=float,default=20);p.add_argument('--offline',action='store_true');a=p.parse_args()
 root=Path(a.project_root).resolve()
 if a.crosswalk:cw=Path(a.crosswalk).resolve()
 else:
  candidates=list((root/'research/p0_s8/s8_22_10_7/results/2023-11-15').glob('*/provisional_game_id_crosswalk.csv'))
  if len(candidates)!=1:raise RuntimeError('Expected one crosswalk; specify --crosswalk')
  cw=candidates[0]
 archive=Path(a.archive).resolve() if a.archive else root/'research/p0_s8/s8_22_10_10/evidence/2023-11-15'
 rows=process(read_csv(cw),archive,not a.offline,a.timeout)
 token=sha(cw.read_bytes())[:16];out=Path(a.output).resolve() if a.output else root/'research/p0_s8/s8_22_10_10/results/2023-11-15'/token
 out.mkdir(parents=True,exist_ok=True);write_csv(out/'game_page_evidence.csv',rows)
 report={'milestone':'S8.22.10.10','crosswalk_sha256':sha(cw.read_bytes()),'target_games':len(rows),'acquisition_counts':dict(Counter(r['acquisition_status'] for r in rows)),'content_counts':dict(Counter(r['content_status'] for r in rows)),'game_ids_independently_certified':0,'historical_asof':'NOT_CERTIFIED','manual_player_reviews_completed':0,'decision':'BLOCK_TRAINING','note':'NBA public page title matches are not independent game ID certification; URL game ID alone is circular evidence. No training promotion.'}
 (out/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('REPORT:',out/'review.json');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
