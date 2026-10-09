"""S7.44 offline article publication metadata inventory. No historical verification promotion."""
import argparse,csv,hashlib,json,re
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

REQUIRED={'candidate_number','player_name','player_id','article_url','article_sha256','tracker_event_date','origin_candidate','destination_candidate','review_status','historical_publication_verified','origin_team_verified'}
FIELDS=['candidate_number','player_name','player_id','tracker_event_date','origin_candidate','destination_candidate','article_url','article_sha256','metadata_field','metadata_raw_value','metadata_normalized_date','metadata_source','publication_candidate_status','event_date_status','source_independence_status','review_status','quality_flags','historical_publication_verified','origin_team_verified']
DATE_KEYS={'datepublished','datecreated','datemodified','article:published_time','article:modified_time','pubdate','publishdate','published','date','dc.date','dc.date.issued','sailthru.date','parsely-pub-date','timestamp'}

class Metadata(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True);self.found=[];self.scripts=[];self.script=False;self.script_buf=[];self.time=False;self.time_buf=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=='meta':
   k=(d.get('property') or d.get('name') or d.get('itemprop') or '').lower().strip()
   if k in DATE_KEYS and d.get('content'):self.found.append((k,d['content'],'HTML_META'))
  if tag=='time':
   if d.get('datetime'):self.found.append(('time.datetime',d['datetime'],'HTML_TIME'))
   self.time=True;self.time_buf=[]
  if tag=='script' and 'ld+json' in d.get('type','').lower():self.script=True;self.script_buf=[]
 def handle_data(self,data):
  if self.script:self.script_buf.append(data)
  if self.time:self.time_buf.append(data)
 def handle_endtag(self,tag):
  if tag=='script' and self.script:
   self.scripts.append(''.join(self.script_buf));self.script=False
  if tag=='time' and self.time:
   value=''.join(self.time_buf).strip()
   if value:self.found.append(('time.text',value,'HTML_TIME_TEXT'))
   self.time=False

def walk_json(v,output):
 if isinstance(v,list):
  for item in v:walk_json(item,output)
 elif isinstance(v,dict):
  for k,value in v.items():
   if k.lower() in ('datepublished','datecreated','datemodified') and isinstance(value,str):output.append((k,value,'JSON_LD'))
   elif isinstance(value,(dict,list)):walk_json(value,output)

def normalize(value):
 value=value.strip()
 if not re.match(r'^\d{4}-\d{2}-\d{2}(?:$|T|\s)',value):return ''
 try:
  d=datetime.strptime(value[:10],'%Y-%m-%d').date()
  return d.isoformat()
 except ValueError:return ''

def extract(html):
 p=Metadata();p.feed(html);items=list(p.found)
 for s in p.scripts:
  try:walk_json(json.loads(s),items)
  except (ValueError,TypeError):continue
 return sorted(set(items))

def run(review_csv,objects_dir,output_dir):
 with Path(review_csv).open(encoding='utf-8-sig',newline='') as f:
  rd=csv.DictReader(f)
  if not rd.fieldnames or not REQUIRED.issubset(rd.fieldnames):raise ValueError('S7.43 schema mismatch')
  rows=list(rd)
 if not rows:raise ValueError('Empty S7.43 review')
 objdir=Path(objects_dir);cache={};out=[];article_summaries={}
 for r in rows:
  if r['historical_publication_verified'].lower()!='false' or r['origin_team_verified'].lower()!='false':raise ValueError('Unexpected upstream verification')
  u=urlsplit(r['article_url'])
  if u.scheme!='https' or u.hostname not in ('nba.com','www.nba.com') or u.username or u.password or u.port not in (None,443):raise ValueError('Non-official URL')
  sha=r['article_sha256']
  if not re.fullmatch('[0-9a-f]{64}',sha):raise ValueError('Invalid article SHA')
  if sha not in cache:
   obj=objdir/(sha+'.html')
   raw=obj.read_bytes()
   if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Article SHA mismatch: '+sha)
   cache[sha]=extract(raw.decode('utf-8',errors='replace'))
  entries=cache[sha]
  candidates={normalize(v) for _,v,_ in entries if normalize(v)}
  # Metadata is self-reported by a retrieved HTML object. It cannot prove historical publication or event date.
  article_summaries.setdefault(sha,{'article_sha256':sha,'article_url':r['article_url'],'candidate_dates':sorted(candidates),'metadata_entries':len(entries)})
  for key,value,source in (entries or [('','','NO_METADATA')]):
   normalized=normalize(value)
   flags=['SELF_REPORTED_ARTICLE_METADATA','HISTORICAL_PUBLICATION_UNVERIFIED'] if entries else ['NO_PUBLICATION_METADATA']
   if len(candidates)>1:flags.append('METADATA_DATES_DISAGREE_OR_DIFFER_IN_PURPOSE')
   if source=='HTML_TIME_TEXT':flags.append('TIME_TEXT_UNATTRIBUTED')
   out.append({'candidate_number':r['candidate_number'],'player_name':r['player_name'],'player_id':r['player_id'],'tracker_event_date':r['tracker_event_date'],'origin_candidate':r['origin_candidate'],'destination_candidate':r['destination_candidate'],'article_url':r['article_url'],'article_sha256':sha,'metadata_field':key,'metadata_raw_value':value,'metadata_normalized_date':normalized,'metadata_source':source,'publication_candidate_status':'UNVERIFIED_SELF_REPORTED' if normalized else 'UNUSABLE_OR_ABSENT','event_date_status':'EVENT_DATE_UNVERIFIED','source_independence_status':'INDEPENDENCE_UNVERIFIED','review_status':'METADATA_REVIEW_ONLY','quality_flags':';'.join(flags),'historical_publication_verified':'false','origin_team_verified':'false'})
 output=Path(output_dir);output.mkdir(parents=True,exist_ok=True)
 with (output/'s7_44_review.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(out)
 report={'milestone':'S7.44','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','input_rows':len(rows),'review_rows':len(out),'unique_article_objects_sha256_verified':len(cache),'articles_with_candidate_dates':sum(bool(x['candidate_dates']) for x in article_summaries.values()),'articles_with_multiple_distinct_candidate_dates':sum(len(x['candidate_dates'])>1 for x in article_summaries.values()),'metadata_source_counts':dict(Counter(x['metadata_source'] for x in out)),'historical_publication_verified':False,'event_dates_verified':0,'event_identity_resolved':0,'independent_reports_verified':0,'eligible_for_asof_training':False,'limitations':['Metadata from current saved HTML is not independent historical publication proof','DatePublished may be revised and dateModified is not original publication','Article publication date does not by itself establish transaction event date','HTML time text may be unrelated to publication','No roster promotion or training']}
 (output/'s7_44_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 (output/'s7_44_article_inventory.json').write_text(json.dumps(sorted(article_summaries.values(),key=lambda x:x['article_url']),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--review-csv',default='research/p0_s4/s7_43/results/s7_43_review.csv');p.add_argument('--objects-dir',default='research/p0_s4/s7_38/results/objects');p.add_argument('--output-dir',default='research/p0_s4/s7_44/results');a=p.parse_args()
 try:print(json.dumps(run(a.review_csv,a.objects_dir,a.output_dir),indent=2))
 except (ValueError,OSError) as e:
  print(json.dumps({'milestone':'S7.44','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(e)}));raise SystemExit(1)
if __name__=='__main__':main()
