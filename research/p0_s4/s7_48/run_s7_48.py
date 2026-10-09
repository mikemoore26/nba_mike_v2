"""S7.48: Offline archived-content recovery, diagnostic only. No training promotion."""
import argparse,csv,hashlib,html,json,re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'research/p0_s4'
INPUT=BASE/'s7_47/results/s7_47_review.csv'
OBJECTS=BASE/'s7_46/results/archive_objects'
OUTPUT=Path(__file__).resolve().parent/'results'
FIELDS=['player_name','origin_candidate','destination_candidate','article_url','archive_timestamp','captured_sha256','hash_verified','archive_original_url_match','s747_evidence_status','recovery_status','best_location','best_excerpt','source_locator','player_in_archived_content','origin_in_excerpt','destination_in_excerpt','action_in_excerpt','direction_candidate','archive_replay_contamination_flag','historical_publication_verified','eligible_for_asof_training','reason']
ALIASES={'ATL':['atlanta','hawks'],'GSW':['golden state','warriors'],'CHA':['charlotte','hornets'],'WAS':['washington','wizards'],'ORL':['orlando','magic'],'LAC':['los angeles clippers','la clippers','clippers'],'IND':['indiana','pacers'],'DAL':['dallas','mavericks']}
def digest(b):return hashlib.sha256(b).hexdigest()
def has_phrase(s,term):return bool(term and re.search(r'(?<!\w)'+re.escape(term)+r'(?!\w)',s,re.I))
def team(s,code):return any(has_phrase(s,a) for a in ALIASES.get((code or '').upper(),[]))
def action(s):return bool(re.search(r'\b(acquir(?:e|ed|es|ing)|trad(?:e|ed|es|ing)|send(?:s|ing)?|deal(?:s|t)?|receiv(?:e|ed|es|ing)|obtain(?:s|ed)?|swap(?:s|ped)?)\b',s,re.I))
def norm(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s or ''))).strip()
def norm_url(s):
 p=urlsplit(s or '');return (p.hostname or '').removeprefix('www.').lower(),p.path.rstrip('/').lower()
class Sections(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True);self.stack=[];self.out=[];self.buf=[];self.kind=None;self.loc='';self.idx=0;self.replay=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs);self.stack.append(tag)
  if tag=='meta':
   key=(a.get('property') or a.get('name') or '').lower();val=a.get('content','')
   if key in ('og:title','twitter:title','title','description','og:description','twitter:description') and val:self.out.append(('META_'+key.upper(),norm(val),'meta:'+key))
  if tag=='script' and (a.get('type','').lower().startswith('application/ld+json')):
   self.kind='JSON_LD';self.buf=[];self.loc=f'script:jsonld:{self.idx}';self.idx+=1
  elif tag in ('title','h1','h2','h3','p','li'):
   self.kind={'title':'TITLE','h1':'HEADING','h2':'HEADING','h3':'HEADING','p':'PARAGRAPH','li':'LIST_ITEM'}[tag];self.buf=[];self.loc=f'{tag}:{self.idx}';self.idx+=1
  if tag in ('nav','footer'):self.replay=True
 def handle_data(self,data):
  if self.kind is not None:self.buf.append(data)
 def handle_endtag(self,tag):
  if self.kind and ((self.kind=='JSON_LD' and tag=='script') or (self.kind!='JSON_LD' and tag in ('title','h1','h2','h3','p','li'))):
   val=''.join(self.buf).strip()
   if val:
    if self.kind=='JSON_LD':
     try:
      obj=json.loads(val)
      def walk(v,path='jsonld'):
       if isinstance(v,dict):
        for k,x in v.items():
         if k in ('headline','description','articleBody','name') and isinstance(x,str) and len(x)<20000:self.out.append(('JSON_LD_'+k.upper(),norm(x),path+'.'+k))
         elif isinstance(x,(dict,list)):walk(x,path+'.'+k)
       elif isinstance(v,list):
        for j,x in enumerate(v[:100]):walk(x,path+f'[{j}]')
      walk(obj)
     except (ValueError,RecursionError):pass
    else:self.out.append((self.kind,norm(val),self.loc))
   self.kind=None;self.buf=[]
  if self.stack:self.stack.pop()
def extract(blob):
 p=Sections();p.feed(blob.decode('utf-8','replace'));return [(k,t,loc) for k,t,loc in p.out if t]
def url_slug(url):return norm(urlsplit(url or '').path.rsplit('/',1)[-1].replace('-',' '))
def classify(excerpts,player,origin,dest,url):
 if not player or not origin or not dest:return ('NO_DIRECTION_PROPOSAL','','','','false','false','false','false','false')
 candidates=[]
 for kind,txt,loc in excerpts:
  if not has_phrase(txt,player):continue
  origin_yes=team(txt,origin);dest_yes=team(txt,dest);action_yes=action(txt)
  # URL slug is diagnostic only; never counts as article-content direction.
  score=(4 if kind in ('PARAGRAPH','JSON_LD_ARTICLEBODY') else 3 if kind in ('HEADING','TITLE','META_OG:TITLE','JSON_LD_HEADLINE') else 1)
  score+=2*origin_yes+2*dest_yes+action_yes
  candidates.append((score,kind,txt,loc,origin_yes,dest_yes,action_yes))
 if not candidates:
  return ('PLAYER_ONLY_IN_URL' if has_phrase(url_slug(url),player) else 'PLAYER_NOT_IN_CAPTURE_CONTENT','','','','false','false','false','false','false')
 candidates.sort(key=lambda v:(-v[0],v[3]))
 _,kind,txt,loc,o,d,a=candidates[0]
 direction=o and d and a
 # Even an apparently full sentence remains review-only; direction grammar not proven.
 status='LOCAL_CLAIM_CANDIDATE_REVIEW_ONLY' if direction else 'PARTIAL_CONTENT_REVIEW_ONLY'
 return status,kind,txt[:450],loc,'true',str(o).lower(),str(d).lower(),str(a).lower(),str(direction).lower()
def load(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def process(input_path=INPUT,objects_dir=OBJECTS,output_dir=OUTPUT):
 source=load(input_path);output_dir.mkdir(parents=True,exist_ok=True);rows=[];seen=set();statuses=Counter();locations=Counter()
 for src in source:
  r={k:'' for k in FIELDS}
  for k in ('player_name','origin_candidate','destination_candidate','article_url','archive_timestamp','captured_sha256','archive_original_url_match'):r[k]=src.get(k,'')
  r.update(s747_evidence_status=src.get('evidence_status',''),historical_publication_verified='false',eligible_for_asof_training='false')
  sha=r['captured_sha256'];capture_status=src.get('source_capture_status','')
  if capture_status!='CAPTURE_SAVED_SHA256':r['recovery_status']='NO_SAVED_CAPTURE';r['reason']='No archived bytes saved; absence not inferred'
  elif not re.fullmatch(r'[a-f0-9]{64}',sha or '') or not (objects_dir/(sha+'.html')).is_file():r['recovery_status']='CAPTURE_MISSING';r['reason']='Missing hash-addressed object'
  else:
   blob=(objects_dir/(sha+'.html')).read_bytes();ok=digest(blob)==sha;r['hash_verified']=str(ok).lower()
   if not ok:r['recovery_status']='HASH_MISMATCH';r['reason']='SHA-256 mismatch; content not inspected'
   elif r['archive_original_url_match']!='true':r['recovery_status']='ORIGINAL_URL_MISMATCH';r['reason']='S7.47 original URL mismatch; content not promoted'
   else:
    seen.add(sha);excerpts=extract(blob)
    status,loc,excerpt,locator,pm,om,dm,am,direction=classify(excerpts,r['player_name'],r['origin_candidate'],r['destination_candidate'],r['article_url'])
    r.update(recovery_status=status,best_location=loc,best_excerpt=excerpt,source_locator=locator,player_in_archived_content=pm,origin_in_excerpt=om,destination_in_excerpt=dm,action_in_excerpt=am,direction_candidate=direction)
    r['archive_replay_contamination_flag']=str(bool(re.search(rb'web\.archive\.org|__wm|wayback toolbar|wm-ipp',blob,re.I))).lower()
    r['reason']='Offline heuristic. HTML replay, body attribution, transaction grammar, archive timestamp and cutoff remain unverified'
    if loc:locations[loc]+=1
  statuses[r['recovery_status']]+=1;rows.append(r)
 with (output_dir/'s7_48_review.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
 report={'milestone':'S7.48','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','input_rows':len(source),'review_rows':len(rows),'sha256_verified_unique_capture_objects':len(seen),'recovery_status_counts':dict(statuses),'best_location_counts':dict(locations),'local_claim_candidates':sum(r['direction_candidate']=='true' for r in rows),'historical_publication_verified':False,'event_dates_verified':0,'independent_reports_verified':0,'eligible_for_asof_training':False,'limitations':['Offline only; archived objects are not altered','Archived URL slug is diagnostic and never proves archived content','Localized player, origin, destination and action co-occurrence is heuristic, not proven transaction direction','Replay-injected and syndicated material may contaminate archive content','No independent timestamp attestation, cutoff proof, roster promotion or training']}
 (output_dir/'s7_48_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=INPUT);p.add_argument('--objects',type=Path,default=OBJECTS);p.add_argument('--output-dir',type=Path,default=OUTPUT);a=p.parse_args();print(json.dumps(process(a.input,a.objects,a.output_dir),indent=2,ensure_ascii=False))
