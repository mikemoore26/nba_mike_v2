"""S7.38: conservatively capture NBA-hosted transaction announcement leads.

Only S7.37 review-only URLs. No transaction or publication-time verification.
"""
import argparse,csv,hashlib,json,re,time,urllib.request,urllib.error
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

FIELDS=['candidate_number','player_name','player_id','event_date','to_team','from_team','article_url','anchor_text','match_basis','review_status','source_sha256','article_sha256','historical_publication_verified']
OUT=['candidate_number','player_name','player_id','event_date','to_team','article_url','capture_status','relevance_status','article_sha256','article_bytes','article_title','excerpt','retrieved_utc','historical_publication_verified','origin_team_verified','source_url']
MAX_BYTES=2_000_000

class VisibleText(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.skip=0;self.text=[];self.in_title=False;self.title=[]
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style','noscript','svg'):self.skip+=1
  if tag=='title':self.in_title=True
 def handle_endtag(self,tag):
  if tag in ('script','style','noscript','svg') and self.skip:self.skip-=1
  if tag=='title':self.in_title=False
 def handle_data(self,data):
  if not self.skip:
   self.text.append(data)
   if self.in_title:self.title.append(data)

def official(url):
 try:
  p=urlsplit(url)
  return p.scheme=='https' and p.hostname in ('www.nba.com','nba.com') and not p.username and not p.password and p.port in (None,443) and not p.query and not p.fragment and (re.fullmatch(r'/news/[a-zA-Z0-9_./-]+',p.path) or re.fullmatch(r'/[a-z0-9-]+/news/[a-zA-Z0-9_./-]+',p.path)) is not None and '..' not in p.path and p.path!='/news/2025-26-nba-trade-tracker'
 except ValueError:return False

def parse_article(raw):
 p=VisibleText();p.feed(raw.decode('utf-8','replace'))
 body=re.sub(r'\s+',' ',' '.join(p.text)).strip()
 title=re.sub(r'\s+',' ',' '.join(p.title)).strip()
 return title,body

def relevant(body,name):
 # Full name with whitespace/apostrophe tolerance; Unicode accents normalized.
 import unicodedata
 def norm(s):
  s=unicodedata.normalize('NFKD',s).casefold();s=''.join(c for c in s if not unicodedata.combining(c));return re.sub(r'[^a-z0-9]+',' ',s).strip()
 n=norm(name);b=norm(body)
 if not n or not re.search(r'(?<![a-z0-9])'+re.escape(n)+r'(?![a-z0-9])',b):return 'PLAYER_NOT_FOUND',''
 terms=re.compile(r'\b(trade|traded|trades|acquire|acquired|acquisition|deal|dealt|send|sent|receive|received)\b')
 if not terms.search(b):return 'TRANSACTION_TERMS_NOT_FOUND',''
 at=b.find(n);return 'RELEVANT_REVIEW_ONLY',b[max(0,at-160):at+len(n)+200]

def load_review(path):
 with Path(path).open(encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f)
  if not reader.fieldnames or not set(FIELDS).issubset(reader.fieldnames):raise ValueError('S7.37 review schema mismatch')
  rows=list(reader)
 if not rows:raise ValueError('Empty S7.37 review')
 for row in rows:
  if row['review_status'] not in ('OFFICIAL_LINK_REVIEW_ONLY','NO_DIRECT_NAME_LINK'):raise ValueError('Unrecognized S7.37 review status')
  if row['review_status']=='OFFICIAL_LINK_REVIEW_ONLY' and not official(row['article_url']):raise ValueError('Untrusted article URL in S7.37 review')
  if row['review_status']=='NO_DIRECT_NAME_LINK' and row['article_url']:raise ValueError('Unmatched candidate contains URL')
  if not re.fullmatch('[0-9a-f]{64}',row['source_sha256']):raise ValueError('Invalid tracker SHA')
  if row['article_sha256'] or row['historical_publication_verified'].lower()!='false':raise ValueError('Prior verification fields must be empty/false')
 return rows

class SafeRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  if not official(newurl):raise ValueError('Redirect to non-approved article URL')
  return super().redirect_request(req,fp,code,msg,headers,newurl)

def network_fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'NBA-MIKE-v2-research/1.0','Accept':'text/html'})
 with urllib.request.build_opener(SafeRedirect).open(req,timeout=18) as response:
  if not official(response.geturl()):raise ValueError('Untrusted final URL')
  if 'text/html' not in response.headers.get('Content-Type','').lower():raise ValueError('Non-HTML content type')
  raw=response.read(MAX_BYTES+1)
  if len(raw)>MAX_BYTES:raise ValueError('Article exceeds byte limit')
  return raw

def run(review_csv,output_dir,limit=12,delay=.5,fetcher=network_fetch):
 if limit<1 or delay<0:raise ValueError('Invalid limit/delay')
 rows=load_review(review_csv);selected=[];seen=set()
 for row in rows:
  if row['review_status']!='OFFICIAL_LINK_REVIEW_ONLY':continue
  key=(row['candidate_number'],row['article_url'])
  if key not in seen:selected.append(row);seen.add(key)
 selected=selected[:limit]
 out=Path(output_dir);out.mkdir(parents=True,exist_ok=True);objects=out/'objects';objects.mkdir(exist_ok=True)
 results=[];counts=Counter();cached={}
 from datetime import datetime,timezone
 for row in selected:
  url=row['article_url'];base={k:row.get(k,'') for k in ('candidate_number','player_name','player_id','event_date','to_team')}
  item=dict(base,article_url=url,capture_status='',relevance_status='',article_sha256='',article_bytes='',article_title='',excerpt='',retrieved_utc='',historical_publication_verified='false',origin_team_verified='false',source_url='https://www.nba.com/news/2025-26-nba-trade-tracker')
  try:
   if url not in cached:
    raw=fetcher(url)
    if not isinstance(raw,bytes) or len(raw)>MAX_BYTES or not raw:raise ValueError('Invalid article bytes')
    if b'<html' not in raw[:4096].lower() and b'<!doctype html' not in raw[:4096].lower():raise ValueError('Non-HTML body')
    sha=hashlib.sha256(raw).hexdigest();target=objects/(sha+'.html')
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=sha:raise ValueError('Object integrity mismatch')
    if not target.exists():target.write_bytes(raw)
    cached[url]=(raw,sha,datetime.now(timezone.utc).isoformat())
    if delay and fetcher is network_fetch:time.sleep(delay)
   raw,sha,when=cached[url];title,body=parse_article(raw)
   label,excerpt=relevant(body,row['player_name'])
   item.update(capture_status='CAPTURED',relevance_status=label,article_sha256=sha,article_bytes=str(len(raw)),article_title=title[:250],excerpt=excerpt[:400],retrieved_utc=when)
  except (OSError,ValueError,TimeoutError,UnicodeError) as e:
   item.update(capture_status='FETCH_FAILED',relevance_status='NOT_EVALUATED',excerpt=(type(e).__name__+': '+str(e))[:300])
  results.append(item);counts[item['capture_status']+':'+item['relevance_status']]+=1
 with (out/'s7_38_review.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=OUT);w.writeheader();w.writerows(results)
 report={'milestone':'S7.38','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','input_review_rows':len(rows),'eligible_lead_rows':len(seen),'attempted_leads':len(selected),'unique_urls_attempted':len({r['article_url'] for r in selected}),'unique_articles_captured':len({r['article_sha256'] for r in results if r['article_sha256']}),'relevant_review_leads':sum(r['relevance_status']=='RELEVANT_REVIEW_ONLY' for r in results),'status_counts':dict(counts),'origin_teams_verified':0,'historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['Full player name and transaction terms may appear in unrelated parts of an article','Capture timestamps show retrieval now, not historical publication','No originating team inferred, no transaction date independently verified','No automatic evidence promotion to S7.31, S7.26, S7.23 or training']}
 (out/'s7_38_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--review-csv',default='research/p0_s4/s7_37/results/s7_37_review.csv');p.add_argument('--output-dir',default='research/p0_s4/s7_38/results');p.add_argument('--limit',type=int,default=12);p.add_argument('--delay',type=float,default=.5);a=p.parse_args()
 try:print(json.dumps(run(a.review_csv,a.output_dir,a.limit,a.delay),indent=2))
 except (ValueError,OSError) as e:
  print(json.dumps({'milestone':'S7.38','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(e)}));raise SystemExit(1)
if __name__=='__main__':main()
