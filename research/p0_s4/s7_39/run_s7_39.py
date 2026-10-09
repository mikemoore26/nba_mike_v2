"""S7.39 offline, hash-checked, local transaction-statement review packets.
No origin verification or historical publication proof. Only S7.38 captured objects.
"""
import argparse,csv,hashlib,json,re,unicodedata
from pathlib import Path
from collections import Counter
from html.parser import HTMLParser
FIELDS=['candidate_number','player_name','player_id','event_date','to_team','article_url','capture_status','relevance_status','article_sha256','article_bytes','article_title','excerpt','retrieved_utc','historical_publication_verified','origin_team_verified','source_url']
OUT=['candidate_number','player_name','player_id','event_date','to_team','article_url','article_sha256','article_title','statement_index','statement','player_mentioned','transaction_term','team_mentions','review_label','review_note','historical_publication_verified','origin_team_verified']
TRANSACTION=re.compile(r'\b(trad(?:e|ed|es|ing)|acquir(?:e|ed|es|ing)|deal|dealt|sent|send|receive[ds]?|exchange[ds]?|swap(?:ped)?)\b',re.I)
TEAMS={'ATL':['atlanta hawks','hawks'],'BOS':['boston celtics','celtics'],'BKN':['brooklyn nets','nets'],'CHA':['charlotte hornets','hornets'],'CHI':['chicago bulls','bulls'],'CLE':['cleveland cavaliers','cavaliers'],'DAL':['dallas mavericks','mavericks'],'DEN':['denver nuggets','nuggets'],'DET':['detroit pistons','pistons'],'GSW':['golden state warriors','warriors'],'HOU':['houston rockets','rockets'],'IND':['indiana pacers','pacers'],'LAC':['los angeles clippers','clippers'],'LAL':['los angeles lakers','lakers'],'MEM':['memphis grizzlies','grizzlies'],'MIA':['miami heat','heat'],'MIL':['milwaukee bucks','bucks'],'MIN':['minnesota timberwolves','timberwolves'],'NOP':['new orleans pelicans','pelicans'],'NYK':['new york knicks','knicks'],'OKC':['oklahoma city thunder','thunder'],'ORL':['orlando magic','magic'],'PHI':['philadelphia 76ers','76ers','sixers'],'PHX':['phoenix suns','suns'],'POR':['portland trail blazers','trail blazers'],'SAC':['sacramento kings','kings'],'SAS':['san antonio spurs','spurs'],'TOR':['toronto raptors','raptors'],'UTA':['utah jazz','jazz'],'WAS':['washington wizards','wizards']}
def norm(s):
 s=unicodedata.normalize('NFKD',s).casefold();return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]+',' ',''.join(c for c in s if not unicodedata.combining(c)))).strip()
class Extract(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.skip=0;self.parts=[];self.title=False;self.head=[]
 def handle_starttag(self,t,a):
  if t in ('script','style','noscript','svg','template'):self.skip+=1
  if t=='title':self.title=True
  if not self.skip and t in ('p','h1','h2','h3','li','blockquote'):self.parts.append('\n')
 def handle_endtag(self,t):
  if t in ('script','style','noscript','svg','template') and self.skip:self.skip-=1
  if t=='title':self.title=False
  if not self.skip and t in ('p','h1','h2','h3','li','blockquote'):self.parts.append('\n')
 def handle_data(self,s):
  if not self.skip:
   self.parts.append(s)
   if self.title:self.head.append(s)
def statements(raw):
 p=Extract();p.feed(raw.decode('utf-8','replace'))
 text=' '.join(p.parts);text=re.sub(r'\s+',' ',text)
 # Sentence boundaries are heuristic and must be reviewed; limit large boilerplate.
 return [s.strip()[:700] for s in re.split(r'(?<=[.!?])\s+(?=[A-Z0-9“\"])',text) if s.strip()][:1500]
def has_name(s,name):
 n=norm(name);return bool(n and re.search(r'(?<![a-z0-9])'+re.escape(n)+r'(?![a-z0-9])',norm(s)))
def teams_in(s):
 n=norm(s);return sorted(k for k,v in TEAMS.items() if any(re.search(r'(?<![a-z0-9])'+re.escape(norm(x))+r'(?![a-z0-9])',n) for x in v))
def load(path):
 with Path(path).open(encoding='utf-8-sig',newline='') as f:
  r=csv.DictReader(f)
  if not r.fieldnames or not set(FIELDS).issubset(r.fieldnames):raise ValueError('S7.38 review schema mismatch')
  rows=list(r)
 if not rows:raise ValueError('Empty S7.38 review')
 for row in rows:
  if row['capture_status'] not in ('CAPTURED','FETCH_FAILED') or row['relevance_status'] not in ('RELEVANT_REVIEW_ONLY','PLAYER_NOT_FOUND','TRANSACTION_TERMS_NOT_FOUND','NOT_EVALUATED'):raise ValueError('Unknown S7.38 status')
  if row['historical_publication_verified'].lower()!='false' or row['origin_team_verified'].lower()!='false':raise ValueError('Upstream verification flag unexpectedly true')
  if row['capture_status']=='CAPTURED' and not re.fullmatch('[0-9a-f]{64}',row['article_sha256']):raise ValueError('Invalid captured SHA')
 return rows
def run(review_csv,objects_dir,output_dir):
 rows=load(review_csv);out=Path(output_dir);obj=Path(objects_dir);result=[];counts=Counter();captured=0;hash_ok=0
 for row in rows:
  if row['capture_status']!='CAPTURED':counts['NOT_CAPTURED']+=1;continue
  captured+=1;sha=row['article_sha256'];path=obj/(sha+'.html')
  if not path.is_file():raise ValueError('Missing captured object: '+sha)
  raw=path.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('SHA mismatch: '+sha)
  if row['article_bytes'] and len(raw)!=int(row['article_bytes']):raise ValueError('Byte length mismatch: '+sha)
  hash_ok+=1
  matches=[]
  for i,s in enumerate(statements(raw),1):
   if not has_name(s,row['player_name']):continue
   if not TRANSACTION.search(s):continue
   matches.append((i,s,teams_in(s)))
  if not matches:
   counts['NO_SAME_SENTENCE_MATCH']+=1
   matches=[(0,'',[])]
  for i,s,teams in matches:
   label='SAME_SENTENCE_REVIEW_ONLY' if i else 'NO_SAME_SENTENCE_MATCH'
   counts[label]+=1
   result.append(dict(candidate_number=row['candidate_number'],player_name=row['player_name'],player_id=row['player_id'],event_date=row['event_date'],to_team=row['to_team'],article_url=row['article_url'],article_sha256=sha,article_title=row['article_title'],statement_index=i,statement=s,player_mentioned=str(bool(i)).lower(),transaction_term=str(bool(i)).lower(),team_mentions=';'.join(teams),review_label=label,review_note='Sentence may be unrelated to candidate event; team names are mentions, not inferred origin/destination',historical_publication_verified='false',origin_team_verified='false'))
 out.mkdir(parents=True,exist_ok=True)
 with (out/'s7_39_review.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=OUT);w.writeheader();w.writerows(result)
 report=dict(milestone='S7.39',status='RESEARCH_ONLY',decision='BLOCK_TRAINING',input_review_rows=len(rows),captured_rows=captured,objects_sha256_verified=hash_ok,review_rows=len(result),same_sentence_review_rows=sum(x['review_label']=='SAME_SENTENCE_REVIEW_ONLY' for x in result),status_counts=dict(counts),origin_teams_verified=0,historical_publication_verified=False,eligible_for_asof_training=False,limitations=['Sentence segmentation is heuristic; text may include navigation or related stories','Team mentions are not verified trade direction or dates','Duplicate article/player records may generate duplicate statements','No automatic promotion to S7.31, S7.26, S7.23 or training'])
 (out/'s7_39_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');return report
def main():
 p=argparse.ArgumentParser();p.add_argument('--review-csv',default='research/p0_s4/s7_38/results/s7_38_review.csv');p.add_argument('--objects-dir',default='research/p0_s4/s7_38/results/objects');p.add_argument('--output-dir',default='research/p0_s4/s7_39/results');a=p.parse_args()
 try:print(json.dumps(run(a.review_csv,a.objects_dir,a.output_dir),indent=2))
 except (ValueError,OSError) as e:print(json.dumps({'milestone':'S7.39','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(e)}));raise SystemExit(1)
if __name__=='__main__':main()
