"""S7.47 offline archived transaction claim review. No evidence promotion."""
import argparse,csv,hashlib,html,json,re
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'research/p0_s4'
INPUT=BASE/'s7_46/results/s7_46_review.csv'
PROPOSALS=BASE/'s7_42/results/s7_42_review.csv'
OBJECTS=BASE/'s7_46/results/archive_objects'
OUTPUT=Path(__file__).resolve().parent/'results'
FIELDS=['player_name','origin_candidate','destination_candidate','article_url','archive_timestamp','capture_time_utc','captured_sha256','hash_verified','archive_original_url_match','source_capture_status','claim_location','claim_excerpt','claim_status','temporal_status','evidence_status','historical_publication_verified','eligible_for_asof_training','reason']
class Visible(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.skip=0;self.parts=[];self.head=[];self.in_head=False
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style','noscript','svg','nav','footer'):self.skip+=1
  if tag=='head':self.in_head=True
  if tag in ('p','h1','h2','h3','article','main','div','li'):self.parts.append('\n')
 def handle_endtag(self,tag):
  if tag in ('script','style','noscript','svg','nav','footer'):self.skip=max(0,self.skip-1)
  if tag=='head':self.in_head=False
  if tag in ('p','h1','h2','h3','article','main','div','li'):self.parts.append('\n')
 def handle_data(self,data):
  if not self.skip and not self.in_head:self.parts.append(data)
def extract_text(blob):
 parser=Visible();parser.feed(blob.decode('utf-8','replace'))
 return '\n'.join(re.sub(r'\s+',' ',s).strip() for s in ''.join(parser.parts).splitlines() if s.strip())
def digest(data):return hashlib.sha256(data).hexdigest()
def norm_url(s):
 p=urlsplit(s or '');return (p.hostname or '').removeprefix('www.').lower(),p.path.rstrip('/').lower()
def capture_dt(ts):
 try:
  if not re.fullmatch(r'\d{14}',ts or ''):return None
  return datetime.strptime(ts,'%Y%m%d%H%M%S').replace(tzinfo=timezone.utc)
 except ValueError:return None
def parse_cutoff(s):
 if not s:return None
 v=datetime.fromisoformat(s.replace('Z','+00:00'))
 if v.tzinfo is None:raise ValueError('Cutoff requires explicit timezone offset')
 return v.astimezone(timezone.utc)
ALIASES={'ATL':['atlanta','hawks'],'GSW':['golden state','warriors'],'CHA':['charlotte','hornets'],'WAS':['washington','wizards'],'ORL':['orlando','magic'],'LAC':['los angeles clippers','la clippers','clippers'],'IND':['indiana','pacers'],'DAL':['dallas','mavericks']}
def team_mentioned(text,code):
 names=ALIASES.get(code.upper(),[])
 return any(re.search(r'(?<!\w)'+re.escape(n)+r'(?!\w)',text,re.I) for n in names)
def evaluate_claim(blob,player,origin,destination):
 if not all((player,origin,destination)):return 'NO_DIRECTION_PROPOSAL','',''
 lines=extract_text(blob).splitlines()
 # Require same short local excerpt; not arbitrary mentions across the page.
 for i,line in enumerate(lines):
  if not re.search(r'(?<!\w)'+re.escape(player)+r'(?!\w)',line,re.I):continue
  near=' '.join(lines[max(0,i-1):min(len(lines),i+2)])[:1200]
  if team_mentioned(near,origin) and team_mentioned(near,destination):
   if re.search(r'\b(acquir(?:e|ed|es)|trad(?:e|ed|es|ing)|send(?:s|ing)?|deal|receive(?:d|s)?)\b',near,re.I):
    return 'LOCAL_DIRECTION_CANDIDATE','BODY_PROXIMITY',near[:400]
   return 'TEAMS_CO_MENTIONED_NO_ACTION','BODY_PROXIMITY',near[:400]
  return 'PLAYER_MENTION_WITHOUT_DIRECTION','BODY',line[:400]
 return 'PLAYER_NOT_IN_VISIBLE_BODY','',''
def load_csv(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def process(input_path=INPUT,proposals_path=PROPOSALS,objects_dir=OBJECTS,output_dir=OUTPUT,cutoff=None):
 captures=load_csv(input_path);proposals=load_csv(proposals_path)
 output_dir.mkdir(parents=True,exist_ok=True)
 byurl={}
 for p in proposals:
  if p.get('origin_candidate') and p.get('destination_candidate'):
   byurl.setdefault(norm_url(p.get('article_url','')),[]).append(p)
 rows=[];verified_objects=set();counts={}
 for cap in captures:
  key=norm_url(cap.get('article_url',''));matches=byurl.get(key,[]) or [None]
  for proposal in matches:
   r=dict.fromkeys(FIELDS,'');r.update(article_url=cap.get('article_url',''),archive_timestamp=cap.get('archive_timestamp',''),capture_time_utc=cap.get('capture_time_utc',''),captured_sha256=cap.get('captured_sha256',''),source_capture_status=cap.get('archive_capture_status',''),historical_publication_verified='false',eligible_for_asof_training='false')
   if proposal:r.update(player_name=proposal.get('player_name',''),origin_candidate=proposal.get('origin_candidate',''),destination_candidate=proposal.get('destination_candidate',''))
   r['archive_original_url_match']=str(bool(cap.get('archive_original_url') and norm_url(cap.get('archive_original_url'))==key)).lower()
   ts=capture_dt(r['archive_timestamp']);r['temporal_status']='NO_CUTOFF_SPECIFIED' if cutoff is None else ('CAPTURE_AT_OR_AFTER_CUTOFF' if ts and ts>=cutoff else 'CAPTURE_BEFORE_CUTOFF' if ts else 'INVALID_CAPTURE_TIMESTAMP')
   sha=r['captured_sha256'];path=objects_dir/(sha+'.html')
   if cap.get('archive_capture_status')!='CAPTURE_SAVED_SHA256':r.update(evidence_status='NO_SAVED_CAPTURE',reason='Capture unavailable; not evidence of absence')
   elif not re.fullmatch('[0-9a-f]{64}',sha or '') or not path.is_file():r.update(evidence_status='CAPTURE_MISSING',reason='Expected hash-addressed HTML object missing')
   else:
    blob=path.read_bytes();ok=digest(blob)==sha;r['hash_verified']=str(ok).lower()
    if not ok:r.update(evidence_status='HASH_MISMATCH',reason='Content differs from saved SHA-256')
    elif r['archive_original_url_match']!='true':r.update(evidence_status='ORIGINAL_URL_MISMATCH',reason='CDX original URL differs from expected article')
    elif ts is None:r.update(evidence_status='INVALID_CAPTURE_TIMESTAMP',reason='Archive timestamp invalid')
    else:
     verified_objects.add(sha)
     status,loc,excerpt=evaluate_claim(blob,r['player_name'],r['origin_candidate'],r['destination_candidate'])
     r.update(claim_status=status,claim_location=loc,claim_excerpt=excerpt)
     r['evidence_status']='CLAIM_CANDIDATE_REVIEW_ONLY' if status=='LOCAL_DIRECTION_CANDIDATE' else 'CONTENT_INSUFFICIENT_REVIEW_ONLY'
     r['reason']='Heuristic archived claim; direction, archive integrity and historical cutoff require separate validation'
   rows.append(r);counts[r['evidence_status']]=counts.get(r['evidence_status'],0)+1
 with (output_dir/'s7_47_review.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
 report={'milestone':'S7.47','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','input_archive_rows':len(captures),'review_rows':len(rows),'sha256_verified_unique_capture_objects':len(verified_objects),'evidence_status_counts':counts,'local_direction_candidates':sum(r['claim_status']=='LOCAL_DIRECTION_CANDIDATE' for r in rows),'cutoff_supplied':cutoff is not None,'historical_publication_verified':False,'event_dates_verified':0,'independent_reports_verified':0,'eligible_for_asof_training':False,'limitations':['No network requests; operates on existing S7.46 saved captures','Local proximity is heuristic, not verified transaction direction','Archive replay can contain inserted or revised content; capture timestamp and content authenticity require review','No capture is promoted to independent historical publication proof','No roster, chronology, or model training promotion']}
 (output_dir/'s7_47_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=INPUT);p.add_argument('--proposals',type=Path,default=PROPOSALS);p.add_argument('--objects',type=Path,default=OBJECTS);p.add_argument('--output-dir',type=Path,default=OUTPUT);p.add_argument('--cutoff',help='ISO8601 with timezone, optional; no implied cutoff');a=p.parse_args()
 print(json.dumps(process(a.input,a.proposals,a.objects,a.output_dir,parse_cutoff(a.cutoff)),indent=2))
