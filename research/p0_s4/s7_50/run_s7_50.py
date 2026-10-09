"""S7.50 offline full archived content recovery and mapping audit. No training promotion."""
import argparse
import csv
import hashlib
import html
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'research/p0_s4'
INPUT = BASE / 's7_49/results/s7_49_review.csv'
ARCHIVE = BASE / 's7_46/results/s7_46_review.csv'
OBJECTS = BASE / 's7_46/results/archive_objects'
OUTPUT = Path(__file__).resolve().parent / 'results'
ALIASES = {'ATL':['atlanta','hawks'],'GSW':['golden state','warriors'],'CHA':['charlotte','hornets'],'WAS':['washington','wizards'],'ORL':['orlando','magic'],'LAC':['los angeles clippers','la clippers','clippers'],'IND':['indiana','pacers'],'DAL':['dallas','mavericks']}
FIELDS = ['player_name','origin_candidate','destination_candidate','mapping_status','mapping_source','article_url','archive_timestamp','captured_sha256','integrity_status','original_url_status','best_location','full_evidence_text','evidence_length','direction_status','transaction_stage','source_family','distinct_capture_objects_same_article','content_contamination_flag','historical_publication_verified','event_date_verified','eligible_for_asof_training','review_reason']

def load(p):
    with p.open(newline='',encoding='utf-8-sig') as f: return list(csv.DictReader(f))

def present(text,term):
    return bool(term and re.search(r'(?<!\w)'+re.escape(term)+r'(?!\w)',text,re.I))

class Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.stack=[];self.buff=[];self.blocks=[];self.jsonld=[];self.title=[];self.meta=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.stack.append((tag,a))
        if tag in ('script','style','noscript','nav','footer','header'): self.skip+=1
        if tag=='meta' and a.get('content') and a.get('property','').lower() in ('og:title','og:description'): self.meta.append((a.get('property'),a['content']))
        if tag in ('p','h1','h2','h3','title','article','div'):self.buff.append([tag,[],len(self.stack)])
        if tag=='script' and a.get('type','').lower()=='application/ld+json':self.jsonld.append([])
    def handle_data(self,data):
        if self.stack and self.stack[-1][0]=='script' and self.stack[-1][1].get('type','').lower()=='application/ld+json' and self.jsonld:self.jsonld[-1].append(data)
        if not self.skip:
            for b in self.buff:b[1].append(data)
    def handle_endtag(self,tag):
        if self.stack:
            # Well-formed HTML is not guaranteed; close matching last tag.
            i=next((i for i in range(len(self.stack)-1,-1,-1) if self.stack[i][0]==tag),None)
            if i is not None:
                depth=i+1
                for b in list(self.buff):
                    if b[2]>=depth:
                        t=' '.join(' '.join(b[1]).split())
                        if t and b[0] in ('p','h1','h2','h3','title') and len(t)<=30000:self.blocks.append((b[0].upper(),t))
                        self.buff.remove(b)
                for old,_ in self.stack[i:]:
                    if old in ('script','style','noscript','nav','footer','header'):self.skip=max(0,self.skip-1)
                del self.stack[i:]

def extract(blob):
    p=Extractor();p.feed(blob.decode('utf-8',errors='replace'))
    out=[]
    for k,v in p.meta:out.append(('META_'+k.upper().replace(':','_'),v))
    for idx,raw in enumerate(p.jsonld):
        try: data=json.loads(''.join(raw))
        except (ValueError,TypeError):continue
        def walk(x):
            if isinstance(x,list):
                for y in x:yield from walk(y)
            elif isinstance(x,dict):
                for k,v in x.items():
                    if k in ('headline','articleBody','description') and isinstance(v,str):yield ('JSONLD_'+k.upper(),v)
                    elif isinstance(v,(dict,list)):yield from walk(v)
        out.extend(walk(data))
    out.extend(p.blocks)
    # Preserve full paragraph/body evidence, not truncated upstream excerpts.
    seen=set();unique=[]
    for kind,text in out:
        text=' '.join(html.unescape(text).split())
        key=(kind,text)
        if text and key not in seen:seen.add(key);unique.append((kind,text))
    return unique

def direction(text,player,origin,dest):
    if not (player and origin and dest and present(text,player)):return 'MAPPING_INCOMPLETE'
    o='(?:'+'|'.join(map(re.escape,ALIASES.get(origin,[])))+')';d='(?:'+'|'.join(map(re.escape,ALIASES.get(dest,[])))+')';p=re.escape(player)
    patterns=[rf'{d}.{{0,100}}\b(?:acquire[ds]?|obtain[sed]*|receive[ds]?)\b.{{0,130}}{p}.{{0,100}}\bfrom\b\s+(?:the\s+)?{o}',rf'{o}.{{0,100}}\b(?:traded?|sent|dealt)\b.{{0,130}}{p}.{{0,100}}\bto\b\s+(?:the\s+)?{d}',rf'{p}.{{0,110}}\b(?:traded|sent|dealt)\b.{{0,90}}\bfrom\b\s+(?:the\s+)?{o}.{{0,100}}\bto\b\s+(?:the\s+)?{d}']
    if any(re.search(x,text,re.I) for x in patterns):return 'FULL_TEXT_DIRECTION_CANDIDATE'
    if any(present(text,x) for x in ALIASES.get(origin,[])) and any(present(text,x) for x in ALIASES.get(dest,[])):return 'COOCCURRENCE_ONLY'
    return 'NO_DIRECTION'

def stage(text):
    if re.search(r'\b(pending|not yet|subject to|awaiting)\b.{0,80}\b(approval|league|physical)|\bnot yet (?:been )?approved\b',text,re.I):return 'PENDING_APPROVAL_LANGUAGE'
    if re.search(r'\b(reportedly|reports? say|agreed to|agreement in principle|expected to)\b',text,re.I):return 'REPORTED_OR_AGREED_LANGUAGE'
    if re.search(r'\b(officially|announced|acquire[ds]?|completed)\b',text,re.I):return 'ANNOUNCEMENT_LANGUAGE_UNVERIFIED'
    return 'STAGE_UNKNOWN'

def valid_url(a,b):
    try:
        x,y=urlsplit(a),urlsplit(b)
        return x.scheme=='https' and y.scheme=='https' and x.hostname==y.hostname and x.path.rstrip('/')==y.path.rstrip('/') and x.query==y.query
    except ValueError:return False

def process(input_path=INPUT,archive_path=ARCHIVE,objects_dir=OBJECTS,output_dir=OUTPUT):
    src=load(input_path);archive=load(archive_path)
    lookup={(r.get('article_url',''),r.get('archive_timestamp',''),r.get('captured_sha256','')):r for r in archive}
    same=Counter((r.get('article_url',''),r.get('captured_sha256','')) for r in archive if r.get('captured_sha256'))
    rows=[]
    for old in src:
        r={k:'' for k in FIELDS}
        for k in ('player_name','origin_candidate','destination_candidate','article_url','archive_timestamp','captured_sha256'):r[k]=old.get(k,'')
        r.update(historical_publication_verified='false',event_date_verified='false',eligible_for_asof_training='false',source_family='NBA_OFFICIAL_ARTICLE_ARCHIVE_UNPROVEN_INDEPENDENCE')
        r['mapping_status']='COMPLETE' if all(r[k] for k in ('player_name','origin_candidate','destination_candidate')) else 'MAPPING_GAP_REVIEW'
        r['mapping_source']='S7_49_UPSTREAM_ONLY' if r['mapping_status']=='COMPLETE' else 'NO_INDEPENDENT_MAPPING'
        # Never invent an origin/destination for Anthony Davis or any other unmapped candidate.
        a=lookup.get((r['article_url'],r['archive_timestamp'],r['captured_sha256']),{})
        r['original_url_status']='EXACT_MATCH' if a and valid_url(r['article_url'],a.get('archive_original_url','')) else 'NOT_VERIFIED'
        sha=r['captured_sha256'];obj=objects_dir/(sha+'.html')
        if not re.fullmatch(r'[a-f0-9]{64}',sha) or not obj.is_file():r['integrity_status']='NO_SAVED_OBJECT';r['review_reason']='Missing or invalid archived object';rows.append(r);continue
        blob=obj.read_bytes()
        if hashlib.sha256(blob).hexdigest()!=sha:r['integrity_status']='HASH_MISMATCH';r['review_reason']='Archived object SHA256 mismatch';rows.append(r);continue
        r['integrity_status']='SHA256_MATCH'
        r['distinct_capture_objects_same_article']=str(len({z.get('captured_sha256') for z in archive if z.get('article_url')==r['article_url'] and z.get('captured_sha256')}))
        r['content_contamination_flag']='REPLAY_MARKERS_PRESENT' if re.search(rb'web\.archive\.org|__wm|wm-ipp',blob,re.I) else 'NO_REPLAY_MARKERS_DETECTED'
        candidates=[]
        for loc,content in extract(blob):
            if not present(content,r['player_name']):continue
            status=direction(content,r['player_name'],r['origin_candidate'],r['destination_candidate'])
            score={'FULL_TEXT_DIRECTION_CANDIDATE':3,'COOCCURRENCE_ONLY':2,'MAPPING_INCOMPLETE':1,'NO_DIRECTION':0}[status]
            candidates.append((score,len(content),loc,content,status))
        if candidates:
            # Favor direction evidence; retain complete evidence text up to 30k characters.
            best=max(candidates,key=lambda z:(z[0],-z[1]));r['best_location']=best[2];r['full_evidence_text']=best[3][:30000];r['evidence_length']=str(len(best[3]));r['direction_status']=best[4];r['transaction_stage']=stage(best[3])
        else:r['direction_status']='NO_PLAYER_IN_EXTRACTED_CONTENT';r['transaction_stage']='NOT_EVALUATED'
        r['review_reason']='Full archived text is a candidate only; archive replay, source independence, event date and as-of availability remain unverified'
        rows.append(r)
    output_dir.mkdir(parents=True,exist_ok=True)
    with (output_dir/'s7_50_review.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    report={'milestone':'S7.50','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','input_rows':len(src),'review_rows':len(rows),'integrity_counts':dict(Counter(r['integrity_status'] for r in rows)),'direction_counts':dict(Counter(r['direction_status'] for r in rows)),'mapping_counts':dict(Counter(r['mapping_status'] for r in rows)),'full_text_direction_candidates':sum(r['direction_status']=='FULL_TEXT_DIRECTION_CANDIDATE' for r in rows),'unique_sha_verified_objects':len({r['captured_sha256'] for r in rows if r['integrity_status']=='SHA256_MATCH'}),'independent_reports_verified':0,'event_dates_verified':0,'historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['No new network requests','Full content text is from archive replay and may include syndicated or injected material','Article URL and same-family captures are not independent source corroboration','Incomplete mapping is never guessed from URL slug','No cutoff or archive timestamp independently attested; training remains blocked']}
    (output_dir/'s7_50_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=INPUT);p.add_argument('--archive',type=Path,default=ARCHIVE);p.add_argument('--objects',type=Path,default=OBJECTS);p.add_argument('--output-dir',type=Path,default=OUTPUT);a=p.parse_args();print(json.dumps(process(a.input,a.archive,a.objects,a.output_dir),indent=2,ensure_ascii=False))
