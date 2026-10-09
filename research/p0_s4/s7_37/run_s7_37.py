"""S7.37: discover official NBA transaction announcement URLs from SHA-verified tracker HTML.

No network activity, no article content verification, no promotion to historical evidence.
"""
import argparse,csv,hashlib,json,re,unicodedata
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin,urlparse,unquote

TRACKER='https://www.nba.com/news/2025-26-nba-trade-tracker'
EXPECTED_SHA='e16458b652fbb5cbdc37188525f3b6fe676060e201c25cca930c6ea2d7865a09'
CANDIDATE_FIELDS={'candidate_number','player_name','player_id','event_date','to_team','from_team','source_sha256'}
CATALOG_FIELDS=['link_number','article_url','host','path','anchor_text','source_sha256','link_class']
REVIEW_FIELDS=['candidate_number','player_name','player_id','event_date','to_team','from_team','article_url','anchor_text','match_basis','review_status','source_sha256','article_sha256','historical_publication_verified']

class Anchors(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.stack=[];self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a':self.stack.append({'href':dict(attrs).get('href',''),'text':[]})
 def handle_data(self,data):
  if self.stack:self.stack[-1]['text'].append(data)
 def handle_endtag(self,tag):
  if tag=='a' and self.stack:
   x=self.stack.pop();self.links.append((x['href'],re.sub(r'\s+',' ',''.join(x['text'])).strip()))

def normalized_tokens(value):
 value=unicodedata.normalize('NFKD',unquote(value).replace('’',"'"))
 value=''.join(c for c in value if not unicodedata.combining(c)).lower()
 return re.findall(r'[a-z0-9]+',value)

def official_article(href):
 """Only NBA-owned news and NBA-hosted team news; no suffix/substring host tricks."""
 try:
  u=urlparse(urljoin(TRACKER,href.strip()))
  if u.scheme!='https' or u.hostname not in ('nba.com','www.nba.com') or u.username or u.password or u.port not in (None,443):return ''
  if u.query or u.fragment:return ''
  path=u.path.rstrip('/')
  if not re.fullmatch(r'/[a-z0-9-]+(?:/news)?/[a-zA-Z0-9_./-]+',path) and not re.fullmatch(r'/news/[a-zA-Z0-9_./-]+',path):return ''
  if not (path.startswith('/news/') or re.fullmatch(r'/[a-z0-9-]+/news/[a-zA-Z0-9_./-]+',path)):return ''
  if path==urlparse(TRACKER).path or path in ('/news','/news/category/top-stories'):return ''
  if path.startswith('/news/category/') or path.startswith('/news/writers-archive'):return ''
  return 'https://www.nba.com'+path
 except ValueError:return ''

def match_player(name,url,anchor):
 tokens=[t for t in normalized_tokens(name) if t not in ('jr','sr','ii','iii','iv')]
 if len(tokens)<2:return ''
 path_tokens=normalized_tokens(urlparse(url).path)
 anchor_tokens=normalized_tokens(anchor)
 # Two distinct substantive name tokens must appear, not a generic single surname.
 if len(set(tokens[:2]))==2 and all(t in path_tokens for t in tokens[:2]):return 'PLAYER_TOKENS_IN_URL'
 if len(set(tokens[:2]))==2 and all(t in anchor_tokens for t in tokens[:2]):return 'PLAYER_TOKENS_IN_ANCHOR'
 return ''

def load_candidates(path,sha):
 with Path(path).open(encoding='utf-8-sig',newline='') as f:
  r=csv.DictReader(f)
  if not r.fieldnames or not CANDIDATE_FIELDS.issubset(r.fieldnames):raise ValueError('S7.30 candidate schema mismatch')
  rows=list(r)
 if not rows or len({x['candidate_number'] for x in rows})!=len(rows):raise ValueError('Empty or duplicate candidates')
 if any(x['source_sha256']!=sha for x in rows):raise ValueError('Candidate tracker SHA mismatch')
 return rows

def discover(tracker_html,review_csv,output_dir,expected_sha=EXPECTED_SHA):
 raw=Path(tracker_html).read_bytes();sha=hashlib.sha256(raw).hexdigest()
 if sha!=expected_sha:raise ValueError('Tracker HTML SHA-256 mismatch')
 if b'<html' not in raw[:2000].lower() and b'<!doctype html' not in raw[:2000].lower():raise ValueError('Tracker not HTML')
 rows=load_candidates(review_csv,sha)
 parser=Anchors();parser.feed(raw.decode('utf-8','replace'))
 links={}
 for href,anchor in parser.links:
  url=official_article(href)
  if url and url not in links:links[url]=anchor
 catalog=[dict(link_number=i,article_url=u,host='www.nba.com',path=urlparse(u).path,anchor_text=a[:300],source_sha256=sha,link_class='OFFICIAL_URL_DISCOVERY_ONLY') for i,(u,a) in enumerate(links.items(),1)]
 results=[];statuses=Counter();matched_players=set()
 for r in rows:
  name=r['player_name'].strip();base={k:r.get(k,'') for k in ('candidate_number','player_name','player_id','event_date','to_team','from_team')}
  found=0
  if name:
   for url,anchor in links.items():
    basis=match_player(name,url,anchor)
    if not basis:continue
    found+=1;matched_players.add(r['candidate_number'])
    results.append(dict(base,article_url=url,anchor_text=anchor[:300],match_basis=basis,review_status='OFFICIAL_LINK_REVIEW_ONLY',source_sha256=sha,article_sha256='',historical_publication_verified='false'))
    statuses['OFFICIAL_LINK_REVIEW_ONLY']+=1
  if not found:
   results.append(dict(base,article_url='',anchor_text='',match_basis='',review_status='NO_DIRECT_NAME_LINK',source_sha256=sha,article_sha256='',historical_publication_verified='false'))
   statuses['NO_DIRECT_NAME_LINK']+=1
 out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
 for file,fields,data in [('s7_37_link_catalog.csv',CATALOG_FIELDS,catalog),('s7_37_review.csv',REVIEW_FIELDS,results)]:
  with (out/file).open('w',encoding='utf-8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(data)
 report={'milestone':'S7.37','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','source_sha256':sha,'input_candidates':len(rows),'official_article_urls_in_tracker':len(catalog),'candidates_with_direct_name_links':len(matched_players),'direct_name_link_rows':statuses['OFFICIAL_LINK_REVIEW_ONLY'],'candidates_without_direct_name_links':statuses['NO_DIRECT_NAME_LINK'],'review_status_counts':dict(statuses),'article_contents_fetched':0,'origin_teams_verified':0,'qualified_s726_events':0,'historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['Official host and URL path identify discovery leads, not independently authenticated article contents','Name tokens in URLs or anchor labels do not prove a transaction or originating team','Direct name matching deliberately misses generic team-labeled announcements; later manual/structured contextual review needed','Tracker capture now does not prove articles were published before historical prediction cutoff','No network fetch and no evidence promotion to S7.31, S7.26, S7.23 or training']}
 (out/'s7_37_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--tracker-html');p.add_argument('--review-csv',default='research/p0_s4/s7_30/results/s7_30_review.csv');p.add_argument('--output-dir',default='research/p0_s4/s7_37/results');a=p.parse_args()
 try:
  if a.tracker_html:source=Path(a.tracker_html)
  else:
   source=Path('research/p0_s4/s7_27/results/objects')/(EXPECTED_SHA+'.html')
  print(json.dumps(discover(source,a.review_csv,a.output_dir),indent=2,ensure_ascii=False))
 except (ValueError,OSError) as e:
  print(json.dumps({'milestone':'S7.37','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(e)}));raise SystemExit(1)
if __name__=='__main__':main()
