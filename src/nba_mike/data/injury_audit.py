"""S7.8 read-only cross-parser quality audit; no training authorization."""
from __future__ import annotations
import csv, json, re
from collections import Counter, defaultdict
from pathlib import Path

REQUIRED=('source_sha256','source_page','player','status','team','matchup','game_date','reason')
TEAM_CODES={'ATL':'Atlanta Hawks','BOS':'Boston Celtics','BKN':'Brooklyn Nets','BRK':'Brooklyn Nets','CHA':'Charlotte Hornets','CHI':'Chicago Bulls','CLE':'Cleveland Cavaliers','DAL':'Dallas Mavericks','DEN':'Denver Nuggets','DET':'Detroit Pistons','GSW':'Golden State Warriors','HOU':'Houston Rockets','IND':'Indiana Pacers','LAC':'LA Clippers','LAL':'Los Angeles Lakers','MEM':'Memphis Grizzlies','MIA':'Miami Heat','MIL':'Milwaukee Bucks','MIN':'Minnesota Timberwolves','NOP':'New Orleans Pelicans','NYK':'New York Knicks','OKC':'Oklahoma City Thunder','ORL':'Orlando Magic','PHI':'Philadelphia 76ers','PHX':'Phoenix Suns','POR':'Portland Trail Blazers','SAC':'Sacramento Kings','SAS':'San Antonio Spurs','TOR':'Toronto Raptors','UTA':'Utah Jazz','WAS':'Washington Wizards'}

def load_csv(path):
    with Path(path).open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        missing=set(REQUIRED)-set(reader.fieldnames or ())
        if missing:raise ValueError(f'{path}: missing columns {sorted(missing)}')
        return list(reader)

def norm(s):return re.sub(r'\s+',' ',str(s or '').strip()).casefold()

def key(r):return (str(r['source_page']),norm(r['player']))

def audit(s74,s76,s77,sha, sample_size=12):
    if not 1<=sample_size<=100:raise ValueError('sample_size must be 1..100')
    datasets={'s7_4':s74,'s7_6':s76,'s7_7':s77}
    for label,rows in datasets.items():
        if any(r['source_sha256']!=sha for r in rows):raise ValueError(f'{label}: source SHA mismatch')
    baselines={label:defaultdict(list) for label in ('s7_4','s7_6')}
    for label in baselines:
        for r in datasets[label]:
            if norm(r['player']):baselines[label][key(r)].append(r)
    duplicate_keys=Counter(key(r) for r in s77 if norm(r['player']))
    issues=[]; missing_dates=[]; mismatches=[]; agreement=Counter(); per_page=defaultdict(lambda:Counter())
    for r in s77:
        page=str(r['source_page']);p=per_page[page];p['records']+=1
        flags=[x for x in r.get('flags','').split('|') if x]
        issue=[]
        if not r['game_date']:
            issue.append('MISSING_GAME_DATE');missing_dates.append({'page':page,'player':r['player'],'matchup':r['matchup'],'team':r['team'],'flags':flags})
            p['missing_dates']+=1
        if r.get('date_provenance')=='DOCUMENT_UNIQUE_DATE_INFERRED':issue.append('INFERRED_DATE');p['inferred_dates']+=1
        if 'INHERITED_COLUMN_LAYOUT_UNVERIFIED' in flags:issue.append('INHERITED_LAYOUT');p['inherited_layout']+=1
        if not r['reason']:issue.append('MISSING_REASON')
        if not r['team'] or not r['matchup']:issue.append('MISSING_TEAM_OR_MATCHUP')
        match=re.fullmatch(r'([A-Z]{2,3})@([A-Z]{2,3})',r['matchup'] or '')
        if match and r['team'] and all(TEAM_CODES.get(code)!=r['team'] for code in match.groups()):issue.append('TEAM_MATCHUP_MISMATCH')
        if duplicate_keys[key(r)]>1:issue.append('DUPLICATE_PLAYER_PAGE')
        comparisons={}
        for label in baselines:
            candidates=baselines[label].get(key(r),[])
            if not candidates:
                comparisons[label]='NO_MATCH';continue
            statuses={norm(x['status']) for x in candidates}
            comparisons[label]='STATUS_MATCH' if norm(r['status']) in statuses else 'STATUS_DISAGREEMENT'
            agreement[f'{label}_{comparisons[label]}']+=1
            if comparisons[label]=='STATUS_DISAGREEMENT':issue.append(label.upper()+'_STATUS_DISAGREEMENT')
        if issue:
            entry={'page':page,'player':r['player'],'status':r['status'],'team':r['team'],'matchup':r['matchup'],'game_date':r['game_date'],'date_provenance':r.get('date_provenance',''),'reason':r['reason'],'flags':flags,'issues':issue,'comparisons':comparisons,'source_y':r.get('source_y','')}
            issues.append(entry)
            if 'TEAM_MATCHUP_MISMATCH' in issue or any('STATUS_DISAGREEMENT' in x for x in issue):mismatches.append(entry)
    severity={'TEAM_MATCHUP_MISMATCH':100,'S7_4_STATUS_DISAGREEMENT':95,'S7_6_STATUS_DISAGREEMENT':95,'DUPLICATE_PLAYER_PAGE':90,'MISSING_TEAM_OR_MATCHUP':80,'MISSING_GAME_DATE':70,'MISSING_REASON':60,'INFERRED_DATE':40,'INHERITED_LAYOUT':20}
    # Spread limited manual sample across pages rather than choosing only page 2.
    ranked=sorted(issues,key=lambda r:(-max(severity.get(x,0) for x in r['issues']),int(r['page']) if r['page'].isdigit() else 999,r['player']))
    by_page=defaultdict(list)
    for r in ranked:by_page[r['page']].append(r)
    sample=[]
    for page in sorted(by_page,key=lambda x:int(x) if x.isdigit() else 999):
        if len(sample)<sample_size:sample.append(by_page[page].pop(0))
    remaining=sorted((r for group in by_page.values() for r in group),key=lambda r:(-max(severity.get(x,0) for x in r['issues']),r['page'],r['player']))
    sample=(sample+remaining)[:sample_size]
    page_summary=[{'page':page,**dict(counts)} for page,counts in sorted(per_page.items(),key=lambda x:int(x[0]))]
    blockers=sum(any(x in r['issues'] for x in ('TEAM_MATCHUP_MISMATCH','S7_4_STATUS_DISAGREEMENT','S7_6_STATUS_DISAGREEMENT','DUPLICATE_PLAYER_PAGE')) for r in issues)
    return {'status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','source_sha256':sha,'counts':{'s7_4':len(s74),'s7_6':len(s76),'s7_7':len(s77),'missing_date':len(missing_dates),'inferred_date':sum(r.get('date_provenance')=='DOCUMENT_UNIQUE_DATE_INFERRED' for r in s77),'issue_records':len(issues),'high_priority_disagreements':blockers,'sample_size':len(sample)},'cross_parser_status_agreement':dict(agreement),'per_page':page_summary,'missing_date_records':missing_dates,'disagreements':mismatches,'review_sample':sample,'limitations':['A match between parsers is not ground truth','No PDF visual verification','Orphan continuation count requires parser-level trace data and cannot be reconstructed from row CSVs','Historical publication timestamp remains unverified','Never training eligible']}

def write_report(report,output_dir):
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    path=out/(report['source_sha256']+'.s7_8_audit.json')
    path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    review=out/(report['source_sha256']+'.s7_8_review_sample.csv')
    with review.open('w',newline='',encoding='utf-8') as f:
        fields=['page','player','status','team','matchup','game_date','date_provenance','reason','issues','flags','source_y','human_verdict','human_notes']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in report['review_sample']:
            w.writerow({**{k:r.get(k,'') for k in fields},'issues':'|'.join(r['issues']),'flags':'|'.join(r['flags']),'human_verdict':'','human_notes':''})
    return path,review
