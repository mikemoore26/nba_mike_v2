"""S7.33 offline audit of S7.32 article relevance; never promotes evidence."""
import argparse,csv,hashlib,html,json,re
from collections import Counter,defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

CAPTURE_REQUIRED={'candidate_number','player_name','player_id','event_date','to_team','article_url','snapshot_path','snapshot_sha256','capture_status'}
REVIEW_REQUIRED={'candidate_number','player_name','player_id','from_team','validation_flags'}
TRANSACTION_TERMS=re.compile(r'\b(trad(?:e|ed|ing)|acquir(?:e|ed|es)|deal|sent to|in exchange for)\b',re.I)
TEAM_WORDS=re.compile(r'\b(?:Hawks|Celtics|Nets|Hornets|Bulls|Cavaliers|Cavs|Mavericks|Mavs|Nuggets|Pistons|Warriors|Rockets|Pacers|Clippers|Lakers|Grizzlies|Heat|Bucks|Timberwolves|Wolves|Pelicans|Knicks|Thunder|Magic|76ers|Sixers|Suns|Trail Blazers|Blazers|Kings|Spurs|Raptors|Jazz|Wizards)\b',re.I)
class VisibleText(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.hidden=0;self.parts=[]
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style','noscript','svg','template'):self.hidden+=1
 def handle_endtag(self,tag):
  if tag in ('script','style','noscript','svg','template'):self.hidden=max(0,self.hidden-1)
 def handle_data(self,data):
  if not self.hidden:self.parts.append(data)

def visible(raw):
 parser=VisibleText();parser.feed(raw.decode('utf-8',errors='replace'))
 return re.sub(r'\s+',' ',html.unescape(' '.join(parser.parts))).strip()

def load_csv(path,required):
 with Path(path).open(newline='',encoding='utf-8-sig') as f:
  reader=csv.DictReader(f)
  if not reader.fieldnames or not required.issubset(reader.fieldnames):raise ValueError('Input schema mismatch: '+str(path))
  return list(reader)

def name_match(name,text):
 # Whole-name match, Unicode apostrophe normalization; no loose surname-only matching.
 normalize=lambda x:re.sub(r'\s+',' ',x.casefold().replace('’',"'").replace('‘',"'"))
 name=normalize(name.strip());text=normalize(text)
 if not name:return False
 return bool(re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',text))

def inspect_snapshot(row,object_root):
 sha=row['snapshot_sha256'].lower().strip()
 if not re.fullmatch('[a-f0-9]{64}',sha):return 'INVALID_SHA','',[]
 # Read only content-addressed objects in configured directory; ignore untrusted CSV paths.
 path=Path(object_root)/(sha+'.html')
 if not path.is_file():return 'SNAPSHOT_MISSING','',[]
 raw=path.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=sha:return 'HASH_MISMATCH','',[]
 text=visible(raw)
 if not name_match(row['player_name'],text):return 'PLAYER_NOT_FOUND',text,[]
 occurrences=[]
 for match in re.finditer(re.escape(row['player_name'].replace('’',"'")),text.replace('’',"'"),re.I):
  snippet=text[max(0,match.start()-240):min(len(text),match.end()+240)]
  occurrences.append(snippet)
  if len(occurrences)>=5:break
 # Keep excerpts for human review, not proof of a transaction.
 if not occurrences:occurrences=[text[:480]]
 return ('PLAYER_AND_TRADE_TERMS_REVIEW' if any(TRANSACTION_TERMS.search(s) for s in occurrences) else 'PLAYER_MENTION_ONLY'),text,occurrences

def audit(capture_csv,review_csv,object_root,out_dir):
 captures=load_csv(capture_csv,CAPTURE_REQUIRED);reviews=load_csv(review_csv,REVIEW_REQUIRED)
 by_id={r['candidate_number']:r for r in reviews}
 if len(by_id)!=len(reviews):raise ValueError('Duplicate review candidate number')
 out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
 captured=[r for r in captures if r['capture_status']=='CAPTURED_REVIEW']
 usage=Counter(r['article_url'] for r in captured)
 results=[];counts=Counter();relevant=set()
 for r in captures:
  cid=r['candidate_number']
  if cid not in by_id:raise ValueError('Capture references unknown candidate '+cid)
  if r['player_id']!=by_id[cid]['player_id']:raise ValueError('Player ID mismatch '+cid)
  status='NOT_CAPTURED';snippets=[];team_mentions=[]
  if r['capture_status']=='CAPTURED_REVIEW':
   status,text,snippets=inspect_snapshot(r,object_root)
   team_mentions=sorted({m.group(0) for s in snippets for m in TEAM_WORDS.finditer(s)},key=str.casefold)
   if status=='PLAYER_AND_TRADE_TERMS_REVIEW':relevant.add(cid)
  counts[status]+=1
  results.append({'candidate_number':cid,'player_name':r['player_name'],'player_id':r['player_id'],'article_url':r['article_url'],'snapshot_sha256':r['snapshot_sha256'],'audit_status':status,'article_reuse_count':usage[r['article_url']] if r['article_url'] else 0,'nearby_team_mentions':' | '.join(team_mentions),'review_excerpt':' | '.join(snippets)[:1200],'origin_team_verified':'false'})
 fields=list(results[0]) if results else ['candidate_number','player_name','player_id','article_url','snapshot_sha256','audit_status','article_reuse_count','nearby_team_mentions','review_excerpt','origin_team_verified']
 with (out/'s7_33_review.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(results)
 missing_origin=sum(not r['from_team'].strip() for r in reviews)
 eligible=sum(bool(r['player_id'].isdigit() and r['player_name'].strip() and not r['from_team'].strip()) for r in reviews)
 report={'milestone':'S7.33','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','review_candidates':len(reviews),'missing_origin_all_rows':missing_origin,'eligible_missing_origin_with_numeric_id_and_name':eligible,'excluded_from_acquisition_eligibility':missing_origin-eligible,'capture_rows':len(captures),'captured_rows':len(captured),'unique_article_urls':len(usage),'article_urls_reused_across_rows':sum(n>1 for n in usage.values()),'max_article_reuse_count':max(usage.values(),default=0),'candidate_players_with_nearby_trade_terms':len(relevant),'audit_status_counts':dict(sorted(counts.items())),'origin_teams_verified':0,'qualified_s726_events':0,'historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['Article mention and nearby trade terms are relevance leads only, not transaction evidence','Team mentions are not originating-team assertions','Article snapshot retrieval does not prove historical publication time','No automatic exports to S7.31, S7.26, or S7.23']}
 (out/'s7_33_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--capture-csv',default='research/p0_s4/s7_32/results/s7_32_capture.csv');p.add_argument('--review-csv',default='research/p0_s4/s7_30/results/s7_30_review.csv');p.add_argument('--object-root',default='research/p0_s4/s7_32/results/objects');p.add_argument('--output-dir',default='research/p0_s4/s7_33/results');a=p.parse_args()
 try:print(json.dumps(audit(a.capture_csv,a.review_csv,a.object_root,a.output_dir),indent=2))
 except (OSError,ValueError) as exc:print(json.dumps({'milestone':'S7.33','status':'FAILED_CLOSED','error':str(exc)}));raise SystemExit(1)
if __name__=='__main__':main()
