"""S7.32 independent official NBA article discovery/capture. Research only."""
import argparse,csv,hashlib,html,json,re,time
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import quote,urlparse,parse_qs,unquote
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

FIELDS=['candidate_number','player_name','player_id','event_date','to_team','article_url','snapshot_path','snapshot_sha256','retrieved_utc','discovery_url','capture_status','error']
NEEDED={'candidate_number','player_name','player_id','event_date','to_team','from_team','validation_flags'}
TRACKER='/news/2025-26-nba-trade-tracker'

def read_review(path):
 with Path(path).open(newline='',encoding='utf-8-sig') as f:
  rd=csv.DictReader(f)
  if not rd.fieldnames or not NEEDED.issubset(rd.fieldnames):raise ValueError('S7.30 review schema mismatch')
  rows=list(rd)
 if len({r['candidate_number'] for r in rows})!=len(rows):raise ValueError('Duplicate candidate numbers')
 return rows

def article_url(value):
 """Only allow original NBA news articles; never accept arbitrary external links."""
 value=html.unescape(value).replace('\\/','/').strip()
 if value.startswith('/news/'):value='https://www.nba.com'+value
 p=urlparse(value)
 if p.scheme!='https' or p.hostname not in ('nba.com','www.nba.com') or p.port not in (None,443):return None
 if not p.path.startswith('/news/') or p.path.rstrip('/')==TRACKER or p.username or p.password:return None
 if not re.fullmatch(r'/news/[A-Za-z0-9_./-]+',p.path):return None
 return 'https://www.nba.com'+p.path.rstrip('/')

def discover(search_html):
 """Links are leads, NOT evidence. NBA search pages can render with no usable links."""
 text=html.unescape(search_html).replace('\\/','/')
 leads=re.findall(r'(?:https://(?:www\.)?nba\.com)?/news/[A-Za-z0-9_./-]+',text)
 found=[]
 for lead in leads:
  url=article_url(lead)
  if url and url not in found:found.append(url)
 return found

def fetch(url,timeout=12,max_bytes=2_000_000):
 req=Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; NBA-MIKE-research/1.0)','Accept':'text/html,application/xhtml+xml'})
 with urlopen(req,timeout=timeout) as resp:
  final=resp.geturl()
  p=urlparse(final)
  if p.scheme!='https' or p.hostname not in ('www.nba.com','nba.com'):
   raise ValueError('Redirected outside NBA domain')
  content_type=resp.headers.get('Content-Type','').lower()
  if 'text/html' not in content_type:raise ValueError('Unexpected content type')
  data=resp.read(max_bytes+1)
  if len(data)>max_bytes:raise ValueError('HTML exceeds size cap')
  return data,final

def safe_capture(url,object_dir,fetcher=fetch):
 if not article_url(url):raise ValueError('Not an official NBA article URL')
 raw,final=fetcher(url)
 if article_url(final)!=article_url(url):raise ValueError('Article redirect mismatch')
 if not raw or not isinstance(raw,bytes):raise ValueError('Missing HTML bytes')
 sha=hashlib.sha256(raw).hexdigest();p=Path(object_dir)/(sha+'.html');p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()!=sha:raise ValueError('Object hash collision')
 if not p.exists():p.write_bytes(raw)
 return str(p),sha

def acquire(review_csv,out_dir,limit=12,per_player=2,delay=0.3,fetcher=fetch,search_fixture_dir=None):
 if limit<1 or per_player<1:raise ValueError('Positive limit and per-player cap required')
 rows=read_review(review_csv)
 eligible=[r for r in rows if r['player_id'].isdigit() and r['player_name'].strip() and not r['from_team'].strip()]
 eligible=eligible[:limit];out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
 results=[];counts=Counter();seen={}
 for r in eligible:
  q=r['player_name']+' '+r['event_date']+' NBA trade'
  discovery_url='https://www.nba.com/search?query='+quote(q)
  base=dict(candidate_number=r['candidate_number'],player_name=r['player_name'],player_id=r['player_id'],event_date=r['event_date'],to_team=r['to_team'],article_url='',snapshot_path='',snapshot_sha256='',retrieved_utc='',discovery_url=discovery_url,capture_status='',error='')
  try:
   if search_fixture_dir:
    raw=(Path(search_fixture_dir)/(r['candidate_number']+'.html')).read_bytes();search_final=discovery_url
   else:
    raw,search_final=fetcher(discovery_url)
   if urlparse(search_final).hostname not in ('nba.com','www.nba.com'):raise ValueError('Search redirect outside NBA')
   search_sha=hashlib.sha256(raw).hexdigest();search_path=out/'objects'/(search_sha+'.html');search_path.parent.mkdir(parents=True,exist_ok=True)
   if not search_path.exists():search_path.write_bytes(raw)
   links=discover(raw.decode('utf-8',errors='replace'))[:per_player]
   if not links:
    results.append(dict(base,capture_status='NO_ARTICLE_LINKS',error='Search response contains no official article links'))
    counts['NO_ARTICLE_LINKS']+=1
   for url in links:
    try:
     if url not in seen:
      seen[url]=safe_capture(url,out/'objects',fetcher=fetcher)
      if not search_fixture_dir and delay:time.sleep(delay)
     path,sha=seen[url]
     results.append(dict(base,article_url=url,snapshot_path=path,snapshot_sha256=sha,retrieved_utc=datetime.now(timezone.utc).isoformat(),capture_status='CAPTURED_REVIEW'))
     counts['CAPTURED_REVIEW']+=1
    except (ValueError,OSError,HTTPError,URLError,TimeoutError) as exc:
     results.append(dict(base,article_url=url,capture_status='ARTICLE_FETCH_FAILED',error=str(exc)[:240]));counts['ARTICLE_FETCH_FAILED']+=1
  except (ValueError,OSError,HTTPError,URLError,TimeoutError) as exc:
   results.append(dict(base,capture_status='SEARCH_FAILED',error=str(exc)[:240]));counts['SEARCH_FAILED']+=1
  if not search_fixture_dir and delay:time.sleep(delay)
 with (out/'s7_32_capture.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(results)
 report=dict(milestone='S7.32',status='RESEARCH_ONLY',decision='BLOCK_TRAINING',input_candidates=len(rows),eligible_missing_origin=len([r for r in rows if r['player_id'].isdigit() and not r['from_team'].strip()]),attempted_candidates=len(eligible),captured_article_rows=counts['CAPTURED_REVIEW'],unique_articles_captured=len(seen),no_article_links=counts['NO_ARTICLE_LINKS'],search_failures=counts['SEARCH_FAILED'],article_failures=counts['ARTICLE_FETCH_FAILED'],origin_teams_verified=0,qualified_s726_events=0,verified_injury_assignments=0,historical_publication_verified=False,eligible_for_asof_training=False,limitations=['Search results are discovery leads, not independent transaction confirmation','Captured articles are not yet parsed or semantically verified for player, originating team or event date','Retrieval time does not prove historical publication or availability','No automatic write to S7.31 evidence or S7.26/S7.23; NBA search may expose no links'])
 (out/'s7_32_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--review-csv',default='research/p0_s4/s7_30/results/s7_30_review.csv');p.add_argument('--output-dir',default='research/p0_s4/s7_32/results');p.add_argument('--limit',type=int,default=12);p.add_argument('--per-player',type=int,default=2);p.add_argument('--delay',type=float,default=0.3);p.add_argument('--search-fixture-dir');a=p.parse_args()
 try:print(json.dumps(acquire(a.review_csv,a.output_dir,a.limit,a.per_player,a.delay,search_fixture_dir=a.search_fixture_dir),indent=2))
 except (ValueError,OSError) as e:
  print(json.dumps({'milestone':'S7.32','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(e)}));raise SystemExit(1)
if __name__=='__main__':main()
