"""S7.36: offline classification of SHA-verified S7.34 RSS URLs; no promotion."""
import argparse,csv,hashlib,html,json,re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse,parse_qs,unquote
from xml.etree import ElementTree as ET

FIELDS=['candidate_number','player_name','rss_item_index','rss_title','raw_url','host','path','source_tier','url_class','filter_reason','possible_unwrapped_url','unwrapped_host','snapshot_sha256']
NBA_HOSTS={'nba.com','www.nba.com'}
TEAM_DOMAINS={'nba.com','www.nba.com'}

def classify_url(url):
 try:
  p=urlparse(html.unescape(url.strip()));host=(p.hostname or '').lower()
  if not host:return 'INVALID','MISSING_HOST',host,''
  if p.scheme not in ('https','http') or p.username or p.password:return 'INVALID','INVALID_SCHEME_OR_CREDENTIALS',host,p.path
  if p.scheme!='https':return 'UNTRUSTED','NOT_HTTPS',host,p.path
  if host in NBA_HOSTS:
   if re.fullmatch(r'/news/[a-zA-Z0-9_./-]+',p.path) and p.path.rstrip('/') not in ('/news','/news/2025-26-nba-trade-tracker'):
    return 'OFFICIAL_NBA','PASSES_EXISTING_FILTER',host,p.path
   return 'OFFICIAL_NBA','OFFICIAL_PATH_EXCLUDED',host,p.path
  if host.endswith('.nba.com'):
   return 'OFFICIAL_NBA_SUBDOMAIN','SUBDOMAIN_EXCLUDED',host,p.path
  if host in ('bing.com','www.bing.com'):
   return 'SEARCH_WRAPPER','BING_URL',host,p.path
  return 'EXTERNAL_UNVERIFIED','NON_NBA_HOST',host,p.path
 except ValueError:return 'INVALID','MALFORMED_URL','',''

def unwrap_hint(url):
 """Display-only. Never fetch or automatically trust an unwrapped target."""
 try:
  p=urlparse(url)
  if p.hostname not in ('bing.com','www.bing.com'):return ''
  for key in ('url','u','r'):
   for val in parse_qs(p.query).get(key,[]):
    candidate=unquote(val)
    if candidate.startswith(('https://','http://')):return candidate[:2000]
 except ValueError:pass
 return ''

def audit(review_csv,object_dir,out_dir):
 with Path(review_csv).open(encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f)
  if not reader.fieldnames or not {'candidate_number','player_name','search_sha256'}.issubset(reader.fieldnames):raise ValueError('Missing S7.34 review fields')
  rows=list(reader)
 if not rows:raise ValueError('Empty review')
 output=Path(out_dir);output.mkdir(parents=True,exist_ok=True)
 results=[];snapshots=[];seen=set();reasons=Counter();tiers=Counter();hosts=Counter()
 for row in rows:
  sha=row['search_sha256'].strip();key=(row['candidate_number'],sha)
  if key in seen:continue
  seen.add(key)
  if not re.fullmatch('[a-f0-9]{64}',sha):raise ValueError('Missing or malformed snapshot SHA for candidate '+row['candidate_number'])
  obj=Path(object_dir)/(sha+'.xml')
  raw=obj.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Snapshot hash mismatch for candidate '+row['candidate_number'])
  root=ET.fromstring(raw)
  if root.tag.rsplit('}',1)[-1].lower()!='rss':raise ValueError('Snapshot not RSS for candidate '+row['candidate_number'])
  items=root.findall('.//item');snapshots.append((row['candidate_number'],sha,len(items)))
  for i,item in enumerate(items,1):
   url=(item.findtext('link') or '').strip();title=(item.findtext('title') or '').strip()
   if not url:continue
   tier,reason,host,path=classify_url(url);hint=unwrap_hint(url)
   hint_host=(urlparse(hint).hostname or '').lower() if hint else ''
   record=dict(candidate_number=row['candidate_number'],player_name=row['player_name'],rss_item_index=i,rss_title=title[:300],raw_url=url,host=host,path=path[:300],source_tier=tier,url_class=reason,filter_reason=reason,possible_unwrapped_url=hint,unwrapped_host=hint_host,snapshot_sha256=sha)
   results.append(record);tiers[tier]+=1;reasons[reason]+=1;hosts[host]+=1
 with (output/'s7_36_url_review.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(results)
 with (output/'s7_36_domain_counts.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.writer(f);w.writerow(['host','rss_link_count']);w.writerows(sorted(hosts.items(),key=lambda p:(-p[1],p[0])))
 report={'milestone':'S7.36','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','snapshots_verified':len(snapshots),'rss_items':sum(x[2] for x in snapshots),'rss_links_classified':len(results),'unique_hosts':len(hosts),'source_tier_counts':dict(sorted(tiers.items())),'filter_reason_counts':dict(sorted(reasons.items())),'top_hosts':[{'host':h,'count':n} for h,n in hosts.most_common(15)],'possible_wrapped_links':sum(bool(x['possible_unwrapped_url']) for x in results),'official_nba_links':sum(t in ('OFFICIAL_NBA','OFFICIAL_NBA_SUBDOMAIN') for t in tiers.elements()),'verified_origin_teams':0,'historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['Offline link classification only; no network fetching','NBA subdomain classification is not authentication of article content','External domains remain unverified, not automatically trustworthy','No promotion to S7.31, S7.26, S7.23 or training']}
 (output/'s7_36_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--review-csv',default='research/p0_s4/s7_34/results/s7_34_review.csv');p.add_argument('--objects-dir',default='research/p0_s4/s7_34/results/objects');p.add_argument('--output-dir',default='research/p0_s4/s7_36/results');a=p.parse_args()
 try:print(json.dumps(audit(a.review_csv,a.objects_dir,a.output_dir),indent=2))
 except (OSError,ValueError,ET.ParseError) as exc:
  print(json.dumps({'milestone':'S7.36','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(exc)}));raise SystemExit(1)
if __name__=='__main__':main()
