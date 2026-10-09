"""S7.42 offline transaction-direction proposals and source-family corroboration audit.
All output is REVIEW_ONLY. Does not verify independent reporting or as-of dates.
"""
import argparse,csv,hashlib,json,re,unicodedata
from pathlib import Path
from collections import Counter,defaultdict
from urllib.parse import urlparse

TEAMS={
'ATL':['atlanta hawks','atlanta','hawks'],'BOS':['boston celtics','boston','celtics'],'BKN':['brooklyn nets','brooklyn','nets'],
'CHA':['charlotte hornets','charlotte','hornets'],'CHI':['chicago bulls','chicago','bulls'],'CLE':['cleveland cavaliers','cleveland','cavaliers'],
'DAL':['dallas mavericks','dallas','mavericks'],'DEN':['denver nuggets','denver','nuggets'],'DET':['detroit pistons','detroit','pistons'],
'GSW':['golden state warriors','golden state','warriors'],'HOU':['houston rockets','houston','rockets'],
'IND':['indiana pacers','indiana','pacers'],'LAC':['los angeles clippers','la clippers','clippers'],
'LAL':['los angeles lakers','lakers'],'MEM':['memphis grizzlies','memphis','grizzlies'],
'MIA':['miami heat','miami','heat'],'MIL':['milwaukee bucks','milwaukee','bucks'],'MIN':['minnesota timberwolves','minnesota','timberwolves'],
'NOP':['new orleans pelicans','new orleans','pelicans'],'NYK':['new york knicks','knicks'],'OKC':['oklahoma city thunder','oklahoma city','thunder'],
'ORL':['orlando magic','orlando','magic'],'PHI':['philadelphia 76ers','philadelphia','76ers'],'PHX':['phoenix suns','phoenix','suns'],
'POR':['portland trail blazers','portland','trail blazers'],'SAC':['sacramento kings','sacramento','kings'],
'SAS':['san antonio spurs','san antonio','spurs'],'TOR':['toronto raptors','toronto','raptors'],
'UTA':['utah jazz','utah','jazz'],'WAS':['washington wizards','washington','wizards']}
# Ambiguous short nicknames are allowed only when unambiguous in a directional slot.
REQ={'candidate_number','player_name','player_id','event_date','to_team','article_url','article_sha256','evidence_type','evidence_text','evidence_sha256','historical_publication_verified','origin_team_verified'}
FIELDS=['candidate_number','player_name','player_id','event_date','tracker_to_team','article_url','article_sha256','source_family','evidence_type','evidence_text','evidence_sha256','origin_candidate','destination_candidate','direction_pattern','review_status','quality_flags','distinct_source_urls','distinct_source_families','historical_publication_verified','origin_team_verified']

def norm(t):
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]+',' ',''.join(c for c in unicodedata.normalize('NFKD',t).casefold() if not unicodedata.combining(c)))).strip()
def has(t,phrase):
    return bool(re.search(r'(?<![a-z0-9])'+re.escape(norm(phrase))+r'(?![a-z0-9])',norm(t)))
def team(t):
    n=norm(t); hits={k for k,v in TEAMS.items() if any(re.search(r'(?<![a-z0-9])'+re.escape(norm(x))+r'(?![a-z0-9])',n) for x in v)}
    return next(iter(hits)) if len(hits)==1 else ''
def family(url):
    u=urlparse(url)
    if u.scheme!='https' or u.netloc.lower() not in ('nba.com','www.nba.com'):raise ValueError('Unapproved article URL')
    parts=[p for p in u.path.split('/') if p]
    if len(parts)>=2 and parts[1]=='news' and parts[0]!='news':return 'TEAM:'+parts[0].lower()
    if parts and parts[0]=='news':return 'NBA_NEWS'
    return 'OTHER_NBA'
def direction(text,player):
    s=norm(text.split('|',1)[0]); name=norm(player)
    if not has(text,player):return ('NONE','','')
    # Headline / sentence: TEAM acquires PLAYER [and PLAYER] from TEAM.
    # Stop at first 'from'; disallow another transfer verb before player.
    for m in re.finditer(r'\b(?:acquire|acquires|acquired)\b',s):
        left=s[:m.start()].strip(); rest=s[m.end():].strip()
        fm=re.search(r'\bfrom\b',rest)
        if not fm:continue
        players=rest[:fm.start()].strip(); source=rest[fm.end():].strip()
        if not has(players,player) or len(players)>180 or re.search(r'\b(?:acquire|acquires|acquired|traded|dealt|sent)\b',players):continue
        dest=team(left[-95:]); origin=team(re.split(r'\b(?:in|for|on|after|with|as|via)\b',source,maxsplit=1)[0][:90])
        if dest and origin and dest!=origin:return ('ACQUIRED_FROM',origin,dest)
    # 'Golden State has acquired PLAYER from Atlanta'
    # 'Indiana has agreed to a deal with LA to acquire PLAYER' intentionally not inferred: LA ambiguous.
    # TEAM trades/sends PLAYER to TEAM.
    for m in re.finditer(r'\b(?:traded|sent|dealt)\b',s):
        left=s[:m.start()].strip(); right=s[m.end():].strip()
        tm=re.search(r'\bto\b',right)
        if not tm or not has(right[:tm.start()],player):continue
        origin=team(left[-95:]);dest=team(re.split(r'\b(?:in|for|on|after|with|as)\b',right[tm.end():],maxsplit=1)[0][:90])
        if origin and dest and origin!=dest:return ('TRADED_TO',origin,dest)
    # 'Pacers trade for Clippers center Ivica Zubac' (strict named possessive team and target player)
    m=re.search(r'^(.*?)\s+trade for\s+(.*?)\s+(?:center|guard|forward|wing)\s+'+re.escape(name)+r'\b',s)
    if m:
        dest,origin=team(m.group(1)),team(m.group(2))
        if dest and origin and dest!=origin:return ('TRADE_FOR_POSITION',origin,dest)
    return ('NONE','','')
def read_csv(path,required):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        rd=csv.DictReader(f)
        if not rd.fieldnames or not required.issubset(rd.fieldnames):raise ValueError('Input schema mismatch')
        rows=list(rd)
    if not rows:raise ValueError('Empty input')
    return rows

def run(review_csv,output_dir,objects_dir=None,s740_csv=None):
    rows=read_csv(review_csv,REQ); out=[];seen=set(); verified=set()
    obj=Path(objects_dir) if objects_dir else None
    for r in rows:
        if r['historical_publication_verified'].lower()!='false' or r['origin_team_verified'].lower()!='false':raise ValueError('Unexpected verified input')
        sha=r['article_sha256']; evidence=r['evidence_text'];esh=r['evidence_sha256']
        if not re.fullmatch('[0-9a-f]{64}',sha) or hashlib.sha256(evidence.encode('utf-8')).hexdigest()!=esh:raise ValueError('Evidence SHA256 mismatch')
        if obj:
            p=obj/(sha+'.html')
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:raise ValueError('Article object SHA256 mismatch')
            verified.add(sha)
        fam=family(r['article_url']); key=(r['candidate_number'],r['player_id'],sha,esh)
        if key in seen:continue
        seen.add(key)
        flags=[]
        if len(evidence)>400 or re.search(r'\b(?:cookie|privacy policy|related stories|subscribe|all rights reserved)\b',evidence,re.I):flags.append('PAGE_CHROME_OR_LONG')
        pattern,origin,dest=direction(evidence,r['player_name']) if not flags else ('NONE','','')
        if not has(evidence,r['player_name']):flags.append('PLAYER_MISSING');pattern,origin,dest='NONE','',''
        if pattern!='NONE' and r['to_team'] and dest!=r['to_team']:flags.append('TRACKER_DESTINATION_CONFLICT')
        out.append({'candidate_number':r['candidate_number'],'player_name':r['player_name'],'player_id':r['player_id'],'event_date':r['event_date'],'tracker_to_team':r['to_team'],'article_url':r['article_url'],'article_sha256':sha,'source_family':fam,'evidence_type':r['evidence_type'],'evidence_text':evidence,'evidence_sha256':esh,'origin_candidate':origin,'destination_candidate':dest,'direction_pattern':pattern,'review_status':'','quality_flags':';'.join(flags),'distinct_source_urls':'0','distinct_source_families':'0','historical_publication_verified':'false','origin_team_verified':'false'})
    groups=defaultdict(list)
    for r in out:
        if r['direction_pattern']!='NONE':groups[(r['candidate_number'],r['player_id'],r['event_date'])].append(r)
    conflict_keys={k for k,v in groups.items() if len({(x['origin_candidate'],x['destination_candidate']) for x in v})>1}
    for r in out:
        key=(r['candidate_number'],r['player_id'],r['event_date']); direction_rows=[x for x in groups[key] if (x['origin_candidate'],x['destination_candidate'])==(r['origin_candidate'],r['destination_candidate'])] if r['direction_pattern']!='NONE' else []
        r['distinct_source_urls']=str(len({x['article_url'] for x in direction_rows}));r['distinct_source_families']=str(len({x['source_family'] for x in direction_rows}))
        flags=set(filter(None,r['quality_flags'].split(';')))
        if key in conflict_keys and r['direction_pattern']!='NONE':r['review_status']='CONFLICT_REVIEW_ONLY'
        elif 'TRACKER_DESTINATION_CONFLICT' in flags:r['review_status']='TRACKER_CONFLICT_REVIEW_ONLY'
        elif flags:r['review_status']='QUALITY_REJECTED'
        elif r['direction_pattern']=='NONE':r['review_status']='CONTEXT_REVIEW_ONLY'
        elif len({x['source_family'] for x in direction_rows})>=2:r['review_status']='MULTI_SOURCE_FAMILY_REVIEW_ONLY'
        else:r['review_status']='DIRECTION_PROPOSAL_REVIEW_ONLY'
    # Compare S7.40 proposals only as diagnostics; no automatic proof.
    old=set()
    if s740_csv and Path(s740_csv).exists():
        oldrows=read_csv(s740_csv,{'candidate_number','player_id','origin_candidate','destination_candidate','review_status'})
        old={(x['candidate_number'],x['player_id'],x['origin_candidate'],x['destination_candidate']) for x in oldrows if x['origin_candidate'] and x['destination_candidate']}
    now={(x['candidate_number'],x['player_id'],x['origin_candidate'],x['destination_candidate']) for x in out if x['origin_candidate'] and x['destination_candidate']}
    target=Path(output_dir);target.mkdir(parents=True,exist_ok=True)
    with (target/'s7_42_review.csv').open('w',encoding='utf-8',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=FIELDS);wr.writeheader();wr.writerows(out)
    counts=dict(Counter(x['review_status'] for x in out))
    report={'milestone':'S7.42','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','input_rows':len(rows),'review_rows':len(out),'duplicate_rows_removed':len(rows)-len(out),'unique_source_objects_sha256_verified':len(verified),'direction_rows':sum(x['direction_pattern']!='NONE' for x in out),'unique_direction_relationships':len(now),'new_relationships_vs_s740':len(now-old),'conflict_groups':len(conflict_keys),'status_counts':counts,'status_totals_reconcile':sum(counts.values())==len(out),'origin_teams_verified':0,'historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['Two source families are corroboration candidates, not proof of editorial independence','Tracker destination conflicts block promotion','Article retrieval date is not historical publication date','No promotion to S7.31, S7.26, S7.23 or training']}
    (target/'s7_42_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--review-csv',default='research/p0_s4/s7_41/results/s7_41_review.csv');p.add_argument('--objects-dir',default='research/p0_s4/s7_38/results/objects');p.add_argument('--s740-csv',default='research/p0_s4/s7_40/results/s7_40_review.csv');p.add_argument('--output-dir',default='research/p0_s4/s7_42/results');a=p.parse_args()
    try:print(json.dumps(run(a.review_csv,a.output_dir,a.objects_dir,a.s740_csv),indent=2))
    except (ValueError,OSError) as e:print(json.dumps({'milestone':'S7.42','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(e)}));raise SystemExit(1)
if __name__=='__main__':main()
