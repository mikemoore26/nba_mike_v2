"""S7.40: conservative offline review of S7.39 evidence statements.

Labels are hypotheses for manual review, never verified transaction evidence.
"""
import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

FIELDS = {'candidate_number','player_name','player_id','event_date','to_team','article_url','article_sha256','article_title','statement_index','statement','player_mentioned','transaction_term','team_mentions','review_label','review_note','historical_publication_verified','origin_team_verified'}
OUT = ['candidate_number','player_name','player_id','event_date','to_team','article_url','article_sha256','statement_sha256','statement','team_mentions','quality_flags','direction_pattern','origin_candidate','destination_candidate','review_status','historical_publication_verified','origin_team_verified']
TEAMS = {'ATL':['atlanta hawks','atlanta','hawks'],'BOS':['boston celtics','celtics'],'BKN':['brooklyn nets','brooklyn'],'CHA':['charlotte hornets','charlotte'],'CHI':['chicago bulls'],'CLE':['cleveland cavaliers'],'DAL':['dallas mavericks'],'DEN':['denver nuggets'],'DET':['detroit pistons'],'GSW':['golden state warriors','golden state'],'HOU':['houston rockets'],'IND':['indiana pacers','indiana'],'LAC':['los angeles clippers','la clippers','l a clippers'],'LAL':['los angeles lakers'],'MEM':['memphis grizzlies'],'MIA':['miami heat'],'MIL':['milwaukee bucks'],'MIN':['minnesota timberwolves'],'NOP':['new orleans pelicans'],'NYK':['new york knicks'],'OKC':['oklahoma city thunder'],'ORL':['orlando magic'],'PHI':['philadelphia 76ers'],'PHX':['phoenix suns'],'POR':['portland trail blazers'],'SAC':['sacramento kings'],'SAS':['san antonio spurs'],'TOR':['toronto raptors'],'UTA':['utah jazz'],'WAS':['washington wizards','washington']}

def normalize(s):
    s = ''.join(c for c in unicodedata.normalize('NFKD',s).casefold() if not unicodedata.combining(c))
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]+',' ',s)).strip()

def team_at(text):
    n = normalize(text)
    hits = {code for code,names in TEAMS.items() if any(re.search(r'(?<![a-z0-9])'+re.escape(normalize(name))+r'(?![a-z0-9])',n) for name in names)}
    return next(iter(hits)) if len(hits)==1 else ''

def has_player(statement,name):
    n=normalize(name); s=normalize(statement)
    return bool(n and re.search(r'(?<![a-z0-9])'+re.escape(n)+r'(?![a-z0-9])',s))

def quality(statement, name, mentions):
    flags=[]
    if not statement or not has_player(statement,name): flags.append('PLAYER_NOT_IN_STATEMENT')
    if len(statement)>400: flags.append('LONG_OR_BOILERPLATE')
    if len([x for x in mentions.split(';') if x])>3: flags.append('MANY_TEAM_MENTIONS')
    if re.search(r'\b(cookie|privacy policy|sign up|related stories|all rights reserved|nba standings|menu|subscribe|advertisement)\b',statement,re.I): flags.append('PAGE_CHROME')
    if re.search(r'\b(?:traded|acquired|sent|dealt|trade|acquire)\b',statement,re.I) is None: flags.append('NO_TRANSACTION_VERB')
    return flags

def direction(statement,name):
    """Only narrow syntactic proposals, not verified evidence. No inference from two teams alone."""
    n = re.escape(normalize(name)); s=normalize(statement)
    # e.g. "Hornets acquire Malaki Branham from Wizards".
    m=re.search(r'(?P<dest>[a-z0-9 ]{3,75}?)\s+(?:have\s+)?(?:acquired|acquire|acquires)\s+'+n+r'\s+from\s+(?P<origin>[a-z0-9 ]{3,75}?)(?:\s+(?:in|as|for|on|after|and|with)\b|$)',s)
    if m:
        origin=team_at(m.group('origin')); dest=team_at(m.group('dest'))
        if origin and dest and origin!=dest:return 'ACQUIRED_FROM',origin,dest
    # e.g. "Hawks traded Buddy Hield to Warriors" (not "in trade with")
    m=re.search(r'(?P<origin>[a-z0-9 ]{3,75}?)\s+(?:have\s+)?(?:traded|sent|dealt)\s+'+n+r'\s+to\s+(?P<dest>[a-z0-9 ]{3,75}?)(?:\s+(?:in|as|for|on|after|and|with)\b|$)',s)
    if m:
        origin=team_at(m.group('origin')); dest=team_at(m.group('dest'))
        if origin and dest and origin!=dest:return 'TRADED_TO',origin,dest
    return 'NONE','',''

def load(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not FIELDS.issubset(reader.fieldnames):raise ValueError('S7.39 review schema mismatch')
        rows=list(reader)
    if not rows:raise ValueError('Empty S7.39 review')
    for row in rows:
        if row['review_label'] not in ('SAME_SENTENCE_REVIEW_ONLY','NO_SAME_SENTENCE_MATCH'):raise ValueError('Invalid upstream label')
        if row['origin_team_verified'].lower()!='false' or row['historical_publication_verified'].lower()!='false':raise ValueError('Unexpected upstream verification')
        if not re.fullmatch(r'[a-f0-9]{64}',row['article_sha256']):raise ValueError('Invalid source hash')
        if row['review_label']=='NO_SAME_SENTENCE_MATCH' and row['statement'].strip():raise ValueError('Unmatched row has evidence text')
    return rows

def run(review_csv,output_dir):
    rows=load(review_csv); out=Path(output_dir)
    result=[]; seen=set(); groups=defaultdict(set); counts=Counter()
    for row in rows:
        statement=row['statement'].strip(); key=(row['candidate_number'],row['article_sha256'],normalize(statement))
        if key in seen:
            counts['DUPLICATE_SKIPPED']+=1
            continue
        seen.add(key)
        flags=quality(statement,row['player_name'],row['team_mentions'])
        pattern,origin,dest=direction(statement,row['player_name']) if not flags else ('NONE','','')
        if pattern!='NONE' and row['to_team'] and dest!=row['to_team']:
            flags.append('DESTINATION_CONFLICT_WITH_TRACKER');pattern,origin,dest='NONE','',''
        status='DIRECTION_PROPOSAL_REVIEW_ONLY' if pattern!='NONE' else ('QUALITY_REJECTED' if flags else 'CONTEXT_REVIEW_ONLY')
        counts[status]+=1
        if pattern!='NONE':groups[(row['candidate_number'],row['player_id'],row['event_date'])].add((origin,dest))
        result.append({**{k:row[k] for k in ('candidate_number','player_name','player_id','event_date','to_team','article_url','article_sha256','statement','team_mentions')},'statement_sha256':hashlib.sha256(statement.encode('utf-8')).hexdigest() if statement else '', 'quality_flags':';'.join(flags),'direction_pattern':pattern,'origin_candidate':origin,'destination_candidate':dest,'review_status':status,'historical_publication_verified':'false','origin_team_verified':'false'})
    conflicts={k for k,v in groups.items() if len(v)>1}
    for r in result:
        if (r['candidate_number'],r['player_id'],r['event_date']) in conflicts and r['review_status']=='DIRECTION_PROPOSAL_REVIEW_ONLY':
            counts['DIRECTION_PROPOSAL_REVIEW_ONLY']-=1
            counts['CONFLICT_REVIEW_ONLY']+=1
            r['review_status']='CONFLICT_REVIEW_ONLY'
    counts={k:v for k,v in counts.items() if v}
    out.mkdir(parents=True,exist_ok=True)
    with (out/'s7_40_review.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=OUT);w.writeheader();w.writerows(result)
    report={'milestone':'S7.40','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','input_review_rows':len(rows),'unique_review_rows':len(result),'duplicates_removed':len(rows)-len(result),'status_counts':dict(Counter(r['review_status'] for r in result)),'direction_proposals':sum(r['review_status']=='DIRECTION_PROPOSAL_REVIEW_ONLY' for r in result),'conflict_groups':len(conflicts),'review_status_sum_matches_rows':sum(Counter(r['review_status'] for r in result).values())==len(result),'origin_teams_verified':0,'historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['Rule-based direction proposals are not independent verification','Original S7.39 summary had a double-counted NO_SAME_SENTENCE_MATCH; S7.40 counts only emitted review rows','Article HTML may contain navigation and related stories; review exact source before using proposals','No historical publication evidence; no promotion to upstream evidence gates or training']}
    (out/'s7_40_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--review-csv',default='research/p0_s4/s7_39/results/s7_39_review.csv');p.add_argument('--output-dir',default='research/p0_s4/s7_40/results');a=p.parse_args()
    try:print(json.dumps(run(a.review_csv,a.output_dir),indent=2))
    except (ValueError,OSError) as e:
        print(json.dumps({'milestone':'S7.40','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(e)}));raise SystemExit(1)
if __name__=='__main__':main()
