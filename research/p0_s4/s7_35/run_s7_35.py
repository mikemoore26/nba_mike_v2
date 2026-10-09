"""S7.35 offline diagnosis of preserved S7.34 search responses; never promotes evidence."""
import argparse,csv,hashlib,html,json,re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse,parse_qs,unquote
from xml.etree import ElementTree as ET

FIELDS=['candidate_number','player_name','capture_status','search_sha256','object_status','content_kind','bytes','rss_item_count','rss_item_links','official_links','rejected_links','rejection_reasons','example_link','diagnosis']
def official(url):
 try:
  p=urlparse(html.unescape(url.strip()))
  return p.scheme=='https' and p.hostname in ('nba.com','www.nba.com') and not p.username and not p.password and (p.port is None or p.port==443) and bool(re.fullmatch(r'/news/[a-zA-Z0-9_./-]+',p.path)) and p.path.rstrip('/') not in ('/news','/news/2025-26-nba-trade-tracker')
 except ValueError:return False
def unwrap(url):
 """Diagnostic only: report possible URL wrappers, never trust them as evidence."""
 p=urlparse(url)
 if p.hostname in ('bing.com','www.bing.com'):
  for k in ('url','u','r'):
   for val in parse_qs(p.query).get(k,[]):
    dec=unquote(val)
    if dec.startswith('http'):return dec
 return url
def classify(raw):
 prefix=raw.lstrip()[:500].lower()
 if prefix.startswith((b'<!doctype html',b'<html')):return 'HTML_NOT_RSS'
 try:root=ET.fromstring(raw)
 except ET.ParseError:return 'INVALID_XML'
 tag=root.tag.rsplit('}',1)[-1].lower()
 return 'RSS' if tag=='rss' else ('ATOM' if tag=='feed' else 'OTHER_XML')
def inspect(raw):
 kind=classify(raw);items=[]
 if kind=='RSS':
  root=ET.fromstring(raw)
  for item in root.findall('.//item'):
   link=(item.findtext('link') or '').strip()
   if link:items.append(link)
 reasons=Counter();accepted=[]
 for link in items:
  if official(link):accepted.append(link)
  else:
   p=urlparse(html.unescape(link));reasons['NON_OFFICIAL_DOMAIN' if p.hostname not in ('nba.com','www.nba.com') else 'OFFICIAL_URL_FILTERED']+=1
 return {'content_kind':kind,'rss_item_count':len(root.findall('.//item')) if kind=='RSS' else 0,'rss_item_links':len(items),'official_links':len(accepted),'rejected_links':len(items)-len(accepted),'rejection_reasons':dict(reasons),'example_link':items[0][:240] if items else ''}
def run(review_csv,object_dir,out_dir):
 rows=list(csv.DictReader(Path(review_csv).open(encoding='utf-8-sig',newline='')))
 if not rows or not {'candidate_number','player_name','search_sha256','capture_status'}.issubset(rows[0]):raise ValueError('S7.34 review missing required columns or rows')
 out=Path(out_dir);out.mkdir(parents=True,exist_ok=True);details=[];stats=Counter();seen=set()
 for row in rows:
  sha=row['search_sha256'].strip();key=(row['candidate_number'],sha)
  if key in seen:continue
  seen.add(key)
  item={k:row.get(k,'') for k in ('candidate_number','player_name','capture_status','search_sha256')}
  item.update(object_status='',content_kind='',bytes=0,rss_item_count=0,rss_item_links=0,official_links=0,rejected_links=0,rejection_reasons='{}',example_link='',diagnosis='')
  if not re.fullmatch('[a-f0-9]{64}',sha):item['object_status']='MISSING_HASH';item['diagnosis']='Search object hash unavailable'
  else:
   path=Path(object_dir)/(sha+'.xml')
   if not path.is_file():item['object_status']='MISSING_OBJECT';item['diagnosis']='Referenced search snapshot not found'
   else:
    raw=path.read_bytes();item['bytes']=len(raw)
    if hashlib.sha256(raw).hexdigest()!=sha:item['object_status']='HASH_MISMATCH';item['diagnosis']='Search snapshot integrity failure'
    else:
     item['object_status']='HASH_OK';d=inspect(raw)
     item.update({k:json.dumps(v,sort_keys=True) if k=='rejection_reasons' else v for k,v in d.items()})
     if d['content_kind']!='RSS':item['diagnosis']='Search response was not RSS; inspect provider response format'
     elif d['rss_item_count']==0:item['diagnosis']='RSS contained zero item elements'
     elif d['rss_item_links']==0:item['diagnosis']='RSS items contained no direct link elements'
     elif d['official_links']==0:item['diagnosis']='RSS links present but all failed official NBA news URL filter'
     else:item['diagnosis']='Official links exist in snapshot; investigate discovery parser/limit'
  stats[item['diagnosis']]+=1;details.append(item)
 with (out/'s7_35_review.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(details)
 report={'milestone':'S7.35','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','candidate_searches_inspected':len(details),'unique_search_snapshots':len({r['search_sha256'] for r in details if r['search_sha256']}),'integrity_ok':sum(r['object_status']=='HASH_OK' for r in details),'diagnosis_counts':dict(sorted(stats.items())),'total_rss_items':sum(r['rss_item_count'] for r in details),'total_rss_links':sum(r['rss_item_links'] for r in details),'total_official_links':sum(r['official_links'] for r in details),'verified_origin_teams':0,'historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['Offline diagnostic only; no new articles or transactions acquired','RSS link filter diagnostics do not prove any transaction','Preserved search snapshots must pass SHA-256 integrity verification','No export or promotion to S7.31, S7.26 or S7.23']}
 (out/'s7_35_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 return report
def main():
 p=argparse.ArgumentParser();p.add_argument('--review-csv',default='research/p0_s4/s7_34/results/s7_34_review.csv');p.add_argument('--objects-dir',default='research/p0_s4/s7_34/results/objects');p.add_argument('--output-dir',default='research/p0_s4/s7_35/results');a=p.parse_args()
 try:print(json.dumps(run(a.review_csv,a.objects_dir,a.output_dir),indent=2))
 except (OSError,ValueError) as e:print(json.dumps({'milestone':'S7.35','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(e)}));raise SystemExit(1)
if __name__=='__main__':main()
