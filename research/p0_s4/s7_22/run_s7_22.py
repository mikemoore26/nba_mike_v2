"""S7.22 semantic context consistency and hard as-of eligibility gate.

Checks recorded section events independently of candidate provenance; it is NOT
independent roster ground truth or historical publication verification.
"""
import argparse,csv,json,re
from collections import Counter
from pathlib import Path

TEAM_CODES = dict(zip(
 ('Atlanta Hawks','Boston Celtics','Brooklyn Nets','Charlotte Hornets','Chicago Bulls','Cleveland Cavaliers','Dallas Mavericks','Denver Nuggets','Detroit Pistons','Golden State Warriors','Houston Rockets','Indiana Pacers','LA Clippers','Los Angeles Lakers','Memphis Grizzlies','Miami Heat','Milwaukee Bucks','Minnesota Timberwolves','New Orleans Pelicans','New York Knicks','Oklahoma City Thunder','Orlando Magic','Philadelphia 76ers','Phoenix Suns','Portland Trail Blazers','Sacramento Kings','San Antonio Spurs','Toronto Raptors','Utah Jazz','Washington Wizards'),
 ('ATL','BOS','BKN','CHA','CHI','CLE','DAL','DEN','DET','GSW','HOU','IND','LAC','LAL','MEM','MIA','MIL','MIN','NOP','NYK','OKC','ORL','PHI','PHX','POR','SAC','SAS','TOR','UTA','WAS')))
FIELDS=('source_sha256','record_id','player','source_page','source_y','game_date','matchup','team','verdict','issues','section_team','section_matchup','section_date')

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def check_row(row, section):
    issues=[]; match=row.get('matchup',''); team=row.get('team','')
    parts=match.split('@')
    if len(parts)!=2 or any(p not in TEAM_CODES.values() for p in parts) or parts[0]==parts[1]:issues.append('INVALID_MATCHUP')
    if team not in TEAM_CODES:issues.append('UNKNOWN_TEAM')
    elif len(parts)==2 and TEAM_CODES[team] not in parts:issues.append('TEAM_NOT_IN_MATCHUP')
    for key in ('game_date','matchup','team'):
        if row.get(key,'') != section.get(key,''):issues.append('SECTION_'+key.upper()+'_MISMATCH')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',row.get('game_date','')):issues.append('INVALID_DATE')
    return issues

def training_allowed(row, historical_publication_verified=False, prediction_cutoff_verified=False, independently_validated=False):
    # Deliberately fail closed. No existing candidate is eligible; future promotion
    # requires explicit upstream evidence plus independent checks.
    return bool(historical_publication_verified and prediction_cutoff_verified and independently_validated and
        row.get('eligible_for_asof_training') is True and row.get('parse_status')=='VERIFIED')

def audit(results_dir,output_dir):
    results_dir=Path(results_dir);output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    details=[]; reports=0; event_files_missing=[]; counters=Counter()
    for candidates in sorted(results_dir.glob('*.s7_14_candidates.csv')):
        sha=candidates.name.split('.')[0]; ev_path=results_dir/(sha+'.s7_14_events.csv')
        if not ev_path.exists():event_files_missing.append(sha);continue
        reports+=1; events=read_csv(ev_path);rows=read_csv(candidates)
        timeline=[]
        for i,e in enumerate(events):
            if e['type'] in ('DATE','MATCHUP','TEAM'):
                timeline.append((int(e['page']),float(e['y']),i,e['type'],e['value']))
        timeline.sort(key=lambda x:(x[0],x[1],x[2]))
        # Events are from the existing extraction pipeline: useful for internal
        # consistency but NOT an independent PDF/roster source.
        rows.sort(key=lambda r:(int(r['source_page']),float(r['source_y'])))
        state={'game_date':'','matchup':'','team':''};idx=0
        for row in rows:
            pos=(int(row['source_page']),float(row['source_y']))
            while idx<len(timeline) and timeline[idx][:2] <= (pos[0],pos[1]+0.01):
                _,_,_,kind,value=timeline[idx]
                if kind=='DATE':state.update(game_date=value,matchup='',team='')
                elif kind=='MATCHUP':state.update(matchup=value,team='')
                else:state['team']=value
                idx+=1
            issues=check_row(row,state)
            if row.get('eligible_for_asof_training','').lower() not in ('false','0',''):
                issues.append('UNEXPECTED_TRAINING_ELIGIBILITY')
            if row.get('parse_status')!='REVIEW_REQUIRED':issues.append('UNEXPECTED_PARSE_STATUS')
            verdict='PASS_INTERNAL_SEMANTICS' if not issues else 'REVIEW_REQUIRED'
            counters['records']+=1;counters['passed']+=not issues;counters['flagged']+=bool(issues)
            counters['cross_page_rows']+=any('p'+str(row['source_page']) not in row.get(k,'') for k in ('team_provenance','matchup_provenance','date_provenance'))
            for issue in issues:counters['issue_'+issue]+=1
            details.append({'source_sha256':sha,'record_id':row['record_id'],'player':row['player'],'source_page':row['source_page'],'source_y':row['source_y'],'game_date':row['game_date'],'matchup':row['matchup'],'team':row['team'],'verdict':verdict,'issues':'|'.join(issues),'section_team':state['team'],'section_matchup':state['matchup'],'section_date':state['game_date']})
    with (output_dir/'s7_22_semantic_checks.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(details)
    gate='PASS_INTERNAL_SEMANTICS' if reports==5 and counters['records']==475 and counters['flagged']==0 and not event_files_missing else 'REVIEW_REQUIRED'
    report={'milestone':'S7.22','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','reports':reports,**dict(counters),'missing_event_files':event_files_missing,'semantic_gate':gate,'historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['Event-based section reconstruction shares upstream extraction; not independent player roster verification','PDF publication-time evidence still missing','No training or source candidate files modified']}
    (output_dir/'s7_22_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--results-dir',default='research/p0_s4/s7_14/results');p.add_argument('--output-dir',default='research/p0_s4/s7_22/results');a=p.parse_args()
    print(json.dumps(audit(a.results_dir,a.output_dir),indent=2))
if __name__=='__main__':main()
