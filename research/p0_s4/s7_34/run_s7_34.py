"""S7.34 targeted official-article discovery. Research only; no evidence promotion."""
import argparse,csv,hashlib,html,json,re,time
from collections import Counter
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote,urlparse
from urllib.request import Request,urlopen
from xml.etree import ElementTree as ET

FIELDS=['candidate_number','player_name','player_id','event_date','to_team','discovery_url','article_url','search_sha256','snapshot_sha256','capture_status','reason','retrieved_utc']
REQUIRED={'candidate_number','player_name','player_id','event_date','to_team','from_team'}
class Visible(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.parts=[];self.hidden=0
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style','noscript','svg','template'):self.hidden+=1
 def handle_endtag(self,tag):
  if tag in ('script','style','noscript','svg','template'):self.hidden=max(0,self.hidden-1)
 def handle_data(self,data):
  if not self.hidden:self.parts.append(data)
def visible(raw):
 p=Visible();p.feed(raw.decode('utf-8',errors='replace'));return re.sub(r'\s+',' ',html.unescape(' '.join(p.parts))).strip()
def norm(s):return re.sub(r'\s+',' ',s.casefold().replace('’',"'").replace('‘',"'")).strip()
def has_name(text,name):
 n=norm(name)
 return bool(n and re.search(r'(?<!\w)'+re.escape(n)+r'(?!\w)',norm(text)))
def canonical(url):
 p=urlparse(html.unescape(url.strip()))
 if p.scheme!='https' or p.hostname not in ('www.nba.com','nba.com') or p.username or p.password or p.port not in (None,443):return None
 if not re.fullmatch(r'/news/[a-zA-Z0-9_./-]+',p.path):return None
 if p.path.rstrip('/') in ('/news','/news/2025-26-nba-trade-tracker'):return None
 return 'https://www.nba.com'+p.path.rstrip('/')
def rss_links(raw):
 try:root=ET.fromstring(raw)
 except ET.ParseError:return []
 found=[]
 for item in root.findall('.//item'):
  link=item.findtext('link') or ''
  u=canonical(link)
  if u and u not in found:found.append(u)
 return found
def fetch(url,timeout=15,max_bytes=2_000_000):
 req=Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; NBA-MIKE-research/1.0)','Accept':'application/rss+xml,text/html,application/xml'})
 with urlopen(req,timeout=timeout) as resp:
  final=resp.geturl();p=urlparse(final)
  if p.scheme!='https' or p.hostname not in ('www.bing.com','bing.com','nba.com','www.nba.com'):raise ValueError('Untrusted redirect')
  data=resp.read(max_bytes+1)
  if len(data)>max_bytes:raise ValueError('Response too large')
  return data,final
def store(raw,obj_dir,suffix):
 sha=hashlib.sha256(raw).hexdigest();p=Path(obj_dir)/(sha+suffix);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()!=sha:raise ValueError('Object hash mismatch')
 if not p.exists():p.write_bytes(raw)
 return sha
def read_review(path):
 with Path(path).open(newline='',encoding='utf-8-sig') as f:
  r=csv.DictReader(f)
  if not r.fieldnames or not REQUIRED.issubset(r.fieldnames):raise ValueError('Review schema mismatch')
  rows=list(r)
 if len({r['candidate_number'] for r in rows})!=len(rows):raise ValueError('Duplicate candidate number')
 return rows
def query_for(row):
 # External search engine only discovers URLs; actual evidence must be official NBA content.
 q=f'site:nba.com/news "{row["player_name"]}" "{row["to_team"]}" trade {row["event_date"]}'
 return 'https://www.bing.com/search?format=rss&q='+quote(q)
def analyze(raw,name):
 text=visible(raw)
 if not has_name(text,name):return 'REJECT_PLAYER_NOT_FOUND'
 if not re.search(r'\b(trad(?:e|ed|ing)|acquir(?:e|ed|es)|transaction|deal)\b',text,re.I):return 'REJECT_NO_TRANSACTION_CONTEXT'
 return 'RELEVANT_REVIEW'
def acquire(review_csv,out_dir,limit=12,max_links=8,delay=0.4,fetcher=fetch,fixture_dir=None):
 if limit<1 or max_links<1:raise ValueError('Positive limits required')
 rows=read_review(review_csv)
 eligible=[r for r in rows if r['player_id'].isdigit() and r['player_name'].strip() and not r['from_team'].strip()]
 selected=eligible[:limit];out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
 records=[];cache={};counts=Counter();unique_relevant=set();searched=set()
 for row in selected:
  url=query_for(row);cid=row['candidate_number'];base={k:row.get(k,'') for k in ('candidate_number','player_name','player_id','event_date','to_team')};base.update(discovery_url=url,article_url='',search_sha256='',snapshot_sha256='',capture_status='',reason='',retrieved_utc='')
  def emit(status,reason='',**kw):
   records.append(dict(base,capture_status=status,reason=reason,**kw));counts[status]+=1
  try:
   if fixture_dir:raw=(Path(fixture_dir)/(cid+'.xml')).read_bytes();final=url
   else:raw,final=fetcher(url)
   if urlparse(final).hostname not in ('bing.com','www.bing.com'):raise ValueError('Search redirected outside Bing')
   search_sha=store(raw,out/'objects','.xml');base['search_sha256']=search_sha
   links=rss_links(raw)[:max_links]
   if not links:emit('NO_OFFICIAL_LINKS','RSS contained no eligible official NBA news URLs')
   for link in links:
    if link not in cache:
     try:
      if fixture_dir:
       fixture=(Path(fixture_dir)/('article_'+hashlib.sha256(link.encode()).hexdigest()+'.html'))
       data=fixture.read_bytes();final_article=link
      else:data,final_article=fetcher(link)
      if canonical(final_article)!=link:raise ValueError('Unexpected article redirect')
      sha=store(data,out/'objects','.html');cache[link]=(data,sha,None)
      if not fixture_dir and delay:time.sleep(delay)
     except (OSError,ValueError,TimeoutError) as exc:cache[link]=(None,'',str(exc)[:200])
    data,sha,error=cache[link]
    if error:emit('ARTICLE_FAILED',error,article_url=link);continue
    status=analyze(data,row['player_name'])
    if status=='RELEVANT_REVIEW':unique_relevant.add(cid)
    emit(status,'Player and transaction term in page; not origin/date proof' if status=='RELEVANT_REVIEW' else 'Page failed strict relevance check',article_url=link,snapshot_sha256=sha,retrieved_utc=datetime.now(timezone.utc).isoformat())
  except (OSError,ValueError,TimeoutError) as exc:emit('SEARCH_FAILED',str(exc)[:200])
  if not fixture_dir and delay:time.sleep(delay)
 with (out/'s7_34_review.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(records)
 report={'milestone':'S7.34','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','input_candidates':len(rows),'missing_origin_all_rows':sum(not r['from_team'].strip() for r in rows),'eligible_missing_origin':len(eligible),'excluded_from_eligibility':sum(not r['from_team'].strip() for r in rows)-len(eligible),'attempted_candidates':len(selected),'unique_official_urls_fetched':sum(bool(v[0]) for v in cache.values()),'candidate_players_with_relevant_leads':len(unique_relevant),'status_counts':dict(sorted(counts.items())),'origin_teams_verified':0,'qualified_s726_events':0,'historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['Bing RSS is discovery only; only official NBA article URLs may be fetched','Relevance requires player full name and transaction language somewhere in page; not necessarily same event','No inferred originating team, verified transaction date, historical publication time, or automatic evidence promotion']}
 (out/'s7_34_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');return report
def main():
 p=argparse.ArgumentParser();p.add_argument('--review-csv',default='research/p0_s4/s7_30/results/s7_30_review.csv');p.add_argument('--output-dir',default='research/p0_s4/s7_34/results');p.add_argument('--limit',type=int,default=12);p.add_argument('--max-links',type=int,default=8);p.add_argument('--delay',type=float,default=.4);p.add_argument('--fixture-dir');a=p.parse_args()
 try:print(json.dumps(acquire(a.review_csv,a.output_dir,a.limit,a.max_links,a.delay,fixture_dir=a.fixture_dir),indent=2))
 except (OSError,ValueError) as exc:print(json.dumps({'milestone':'S7.34','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(exc)}));raise SystemExit(1)
if __name__=='__main__':main()
