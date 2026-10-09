"""S7.41 offline recovery of review-only transaction leads from saved S7.38 HTML.
Never verifies origins, publication timing, or historical roster eligibility.
"""
import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path

INPUT_REQUIRED = {'candidate_number','player_name','player_id','event_date','to_team','article_url','capture_status','article_sha256','article_bytes','historical_publication_verified','origin_team_verified'}
OUTPUT = ['candidate_number','player_name','player_id','event_date','to_team','article_url','article_sha256','evidence_type','evidence_text','evidence_sha256','origin_candidate','destination_candidate','direction_pattern','review_status','quality_flags','historical_publication_verified','origin_team_verified']
TEAMS = {'ATL':('atlanta hawks','atlanta','hawks'),'BOS':('boston celtics','boston'),'BKN':('brooklyn nets','brooklyn'),'CHA':('charlotte hornets','charlotte','hornets'),'CHI':('chicago bulls','chicago'),'CLE':('cleveland cavaliers','cleveland'),'DAL':('dallas mavericks','dallas'),'DEN':('denver nuggets','denver'),'DET':('detroit pistons','detroit'),'GSW':('golden state warriors','golden state','warriors'),'HOU':('houston rockets','houston'),'IND':('indiana pacers','indiana','pacers'),'LAC':('los angeles clippers','la clippers','clippers'),'LAL':('los angeles lakers','lakers'),'MEM':('memphis grizzlies','memphis'),'MIA':('miami heat','miami'),'MIL':('milwaukee bucks','milwaukee'),'MIN':('minnesota timberwolves','minnesota'),'NOP':('new orleans pelicans','new orleans'),'NYK':('new york knicks','knicks'),'OKC':('oklahoma city thunder','oklahoma city'),'ORL':('orlando magic','orlando','magic'),'PHI':('philadelphia 76ers','philadelphia'),'PHX':('phoenix suns','phoenix'),'POR':('portland trail blazers','portland'),'SAC':('sacramento kings','sacramento'),'SAS':('san antonio spurs','san antonio'),'TOR':('toronto raptors','toronto'),'UTA':('utah jazz','utah'),'WAS':('washington wizards','washington','wizards')}
VERBS = re.compile(r'\b(?:acquire[ds]?|traded?|dealt|sent|receive[ds]?)\b', re.I)
CHROME = re.compile(r'\b(?:cookie|privacy policy|related stories|subscribe|sign up|advertisement|terms of use|all rights reserved)\b',re.I)

def norm(text):
    text = ''.join(c for c in unicodedata.normalize('NFKD',text).casefold() if not unicodedata.combining(c))
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]+',' ',text)).strip()

def contains(text,phrase):
    n,p=norm(text),norm(phrase)
    return bool(p and re.search(r'(?<![a-z0-9])'+re.escape(p)+r'(?![a-z0-9])',n))

def team_in(text):
    hits=[code for code,aliases in TEAMS.items() if any(contains(text,a) for a in aliases)]
    return hits[0] if len(hits)==1 else ''

def direction(text,player):
    s=norm(text); name=re.escape(norm(player))
    if re.search(r'\bfrom\b.{0,85}\band\b',s):return 'NONE','',''
    # Explicit origin and destination only; do not infer from two names in proximity.
    for verb in ('acquired','acquire','acquires'):
        m=re.search(r'(?P<dest>[a-z0-9 ]{3,85}?)\s+'+verb+r'\s+'+name+r'\s+from\s+(?P<origin>[a-z0-9 ]{3,85}?)(?=\s+(?:in|for|on|after|with|as|and)\b|$)',s)
        if m:
            origin,dest=team_in(m['origin']),team_in(m['dest'])
            if origin and dest and origin!=dest:return 'ACQUIRED_FROM',origin,dest
    m=re.search(r'(?P<origin>[a-z0-9 ]{3,85}?)\s+(?:traded|sent|dealt)\s+'+name+r'\s+to\s+(?P<dest>[a-z0-9 ]{3,85}?)(?=\s+(?:in|for|on|after|with|as|and)\b|$)',s)
    if m:
        origin,dest=team_in(m['origin']),team_in(m['dest'])
        if origin and dest and origin!=dest:return 'TRADED_TO',origin,dest
    return 'NONE','',''

class Blocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack=[];self.skip=0;self.blocks=[];self.active=[];self.meta=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='meta' and attrs.get('property','').lower() in ('og:title','twitter:title') and attrs.get('content'):
            self.meta.append(attrs['content'])
        if tag in ('script','style','noscript','svg','template','nav','footer','aside'):
            self.skip+=1
        if not self.skip and tag in ('h1','p','h2'):
            self.active.append([tag,[],bool('article' in self.stack or 'main' in self.stack)])
        if tag in ('article','main'):self.stack.append(tag)
    def handle_endtag(self,tag):
        if self.active and self.active[-1][0]==tag:
            kind,parts,inside=self.active.pop()
            text=re.sub(r'\s+',' ',' '.join(parts)).strip()
            if text:self.blocks.append((kind,text,inside))
        if tag in ('article','main') and self.stack:self.stack.pop()
        if tag in ('script','style','noscript','svg','template','nav','footer','aside') and self.skip:self.skip-=1
    def handle_data(self,data):
        if not self.skip:
            for item in self.active:item[1].append(data)

def extract(raw):
    parser=Blocks();parser.feed(raw.decode('utf-8','replace'))
    headings=[('HEADLINE',x) for x in parser.meta]
    headings += [('HEADLINE',txt) for tag,txt,_ in parser.blocks if tag=='h1']
    paragraphs=[('ARTICLE_PARAGRAPH',txt) for tag,txt,inside in parser.blocks if tag=='p' and inside]
    if not paragraphs:paragraphs=[('PAGE_PARAGRAPH',txt) for tag,txt,_ in parser.blocks if tag=='p']
    result=[];seen=set()
    for typ,txt in headings+paragraphs[:30]:
        key=norm(txt)
        if key not in seen:seen.add(key);result.append((typ,txt))
    return result

def load(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not INPUT_REQUIRED.issubset(reader.fieldnames):raise ValueError('S7.38 review schema mismatch')
        rows=list(reader)
    if not rows:raise ValueError('Empty S7.38 review')
    for row in rows:
        if row['historical_publication_verified'].lower()!='false' or row['origin_team_verified'].lower()!='false':raise ValueError('Unexpected verified upstream evidence')
        if row['capture_status'] not in ('CAPTURED','FETCH_FAILED'):raise ValueError('Unknown capture status')
        if row['capture_status']=='CAPTURED' and not re.fullmatch('[0-9a-f]{64}',row['article_sha256']):raise ValueError('Invalid SHA256')
    return rows

def run(review_csv,objects_dir,output_dir):
    rows=load(review_csv);objects=Path(objects_dir);out=Path(output_dir)
    result=[];seen=set();verified=set();counts=Counter();groups=defaultdict(set)
    for row in rows:
        if row['capture_status']!='CAPTURED':counts['not_captured']+=1;continue
        sha=row['article_sha256'];raw_path=objects/(sha+'.html')
        if not raw_path.is_file():raise ValueError('Missing source object: '+sha)
        raw=raw_path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Source SHA256 mismatch: '+sha)
        if row['article_bytes'] and len(raw)!=int(row['article_bytes']):raise ValueError('Source byte count mismatch: '+sha)
        verified.add(sha)
        leads=0
        for typ,txt in extract(raw):
            if not contains(txt,row['player_name']) or not VERBS.search(txt):continue
            key=(row['candidate_number'],sha,norm(txt))
            if key in seen:counts['duplicate_leads_skipped']+=1;continue
            seen.add(key);leads+=1
            flags=[]
            if len(txt)>400:flags.append('OVERSIZED_TEXT')
            if CHROME.search(txt):flags.append('PAGE_CHROME')
            pattern,origin,dest=direction(txt,row['player_name']) if not flags else ('NONE','','')
            if pattern!='NONE' and row['to_team'] and dest!=row['to_team']:
                flags.append('TRACKER_DESTINATION_CONFLICT');pattern,origin,dest='NONE','',''
            status='DIRECTION_PROPOSAL_REVIEW_ONLY' if pattern!='NONE' else ('QUALITY_REJECTED' if flags else 'CONTEXT_REVIEW_ONLY')
            if pattern!='NONE':groups[(row['candidate_number'],row['player_id'],row['event_date'])].add((origin,dest))
            result.append({'candidate_number':row['candidate_number'],'player_name':row['player_name'],'player_id':row['player_id'],'event_date':row['event_date'],'to_team':row['to_team'],'article_url':row['article_url'],'article_sha256':sha,'evidence_type':typ,'evidence_text':txt,'evidence_sha256':hashlib.sha256(txt.encode('utf-8')).hexdigest(),'origin_candidate':origin,'destination_candidate':dest,'direction_pattern':pattern,'review_status':status,'quality_flags':';'.join(flags),'historical_publication_verified':'false','origin_team_verified':'false'})
        if not leads:counts['captured_rows_without_leads']+=1
    conflicts={k for k,v in groups.items() if len(v)>1}
    for item in result:
        key=(item['candidate_number'],item['player_id'],item['event_date'])
        if key in conflicts and item['review_status']=='DIRECTION_PROPOSAL_REVIEW_ONLY':item['review_status']='CONFLICT_REVIEW_ONLY'
    out.mkdir(parents=True,exist_ok=True)
    with (out/'s7_41_review.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=OUTPUT);writer.writeheader();writer.writerows(result)
    status_counts=dict(Counter(r['review_status'] for r in result))
    report={'milestone':'S7.41','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','input_rows':len(rows),'unique_source_objects_sha256_verified':len(verified),'review_rows':len(result),'status_counts':status_counts,'status_totals_reconcile':sum(status_counts.values())==len(result),'direction_proposals':status_counts.get('DIRECTION_PROPOSAL_REVIEW_ONLY',0),'conflict_groups':len(conflicts),'diagnostic_counts':dict(counts),'origin_teams_verified':0,'historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['Headline/paragraph extraction is heuristic and may contain related stories','Direction candidates are syntactic review proposals, not independent corroboration','Headline-only claims require supporting body evidence and historical publication proof','No promotion to S7.31, S7.26, S7.23 or training']}
    (out/'s7_41_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--review-csv',default='research/p0_s4/s7_38/results/s7_38_review.csv')
    parser.add_argument('--objects-dir',default='research/p0_s4/s7_38/results/objects')
    parser.add_argument('--output-dir',default='research/p0_s4/s7_41/results')
    args=parser.parse_args()
    try:print(json.dumps(run(args.review_csv,args.objects_dir,args.output_dir),indent=2))
    except (ValueError,OSError) as exc:
        print(json.dumps({'milestone':'S7.41','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(exc)}));raise SystemExit(1)
if __name__=='__main__':main()
