"""Acquire adjacent-game ESPN evidence for the 35 missing 2023-11-15 candidates.

Never certify membership, NBA identity, injury status, or 2023-11-15 as-of status.
"""
import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import io
import json
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

TARGET='2023-11-15'
DEFAULT_DATES=('2023-11-14','2023-11-16','2023-11-17','2023-11-18')
API='https://site.api.espn.com/apis/site/v2/sports/basketball/nba'
FIELDS=['record_id','raw_name','candidate_nba_person_id','report_team','target_day_classification','adjacent_classification','adjacent_dates','adjacent_teams','matching_espn_athlete_ids','evidence_ids','historical_team_verified','training_decision']

def digest(data):return hashlib.sha256(data).hexdigest()
def encode(obj):return (json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode('utf-8')
def immutable(path,data):
    if path.exists():
        if path.read_bytes()!=data:raise ValueError('Immutable evidence conflict: '+str(path))
    else:path.write_bytes(data)

def load_s824_module(root):
    p=root/'research/p0_s8/s8_22_10_24/run_s8_22_10_24.py'
    if not p.is_file():raise ValueError('Missing S8.22.10.24 script')
    spec=importlib.util.spec_from_file_location('s824_for_s825',p)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def load_predecessor(root):
    base=root/'research/p0_s8/s8_22_10_24/results'/TARGET
    manifests=list(base.glob('*/review.json'))
    if len(manifests)!=1:raise ValueError(f'Expected one S8.22.10.24 report; got {len(manifests)}')
    path=manifests[0];m=json.loads(path.read_text(encoding='utf-8'))
    if m.get('milestone')!='S8.22.10.24' or m.get('training_decision')!='BLOCK_TRAINING' or m.get('player_candidates')!=44 or m.get('historical_team_verified')!=0:raise ValueError('Predecessor governance mismatch')
    for e in m['evidence_documents']:
        p=path.parent/e['relative_path']
        if not p.is_file() or digest(p.read_bytes())!=e['sha256']:raise ValueError('Predecessor evidence integrity mismatch')
    for name,key in [('historical_team_boxscore_review.csv','review_csv_sha256'),('boxscore_listings.json','boxscore_listings_sha256')]:
        p=path.parent/name
        if not p.is_file() or digest(p.read_bytes())!=m[key]:raise ValueError('Predecessor output integrity mismatch')
    with (path.parent/'historical_team_boxscore_review.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    if len(rows)!=44 or len({r['record_id'] for r in rows})!=44:raise ValueError('Invalid predecessor rows')
    if Counter(r['classification'] for r in rows)!=Counter({'NO_BOX_SCORE_LISTING_NOT_NEGATIVE_PROOF':35,'SAME_TEAM_BOX_SCORE_LISTING_UNCERTIFIED':9}):raise ValueError('Unexpected predecessor baseline; review before running')
    cap=root/'research/p0_s8/s8_22_10_22a/results'/TARGET
    candidates=[]
    for p in cap.glob('*/capture_manifest.json'):
        cm=json.loads(p.read_text(encoding='utf-8'))
        cp=p.parent/'player_id_candidates.csv'
        if cm.get('milestone')=='S8.22.10.22A' and cp.is_file() and digest(cp.read_bytes())==m['predecessor_candidate_sha256']:
            with cp.open(encoding='utf-8-sig',newline='') as f:candidates.append(list(csv.DictReader(f)))
    if len(candidates)!=1 or len(candidates[0])!=44:raise ValueError('Missing uniquely authenticated candidate set')
    return path,m,rows,candidates[0]

def validate_dates(dates):
    if not dates or len(dates)>7 or len(set(dates))!=len(dates):raise ValueError('Supply 1-7 distinct adjacent dates')
    target=dt.date.fromisoformat(TARGET)
    for value in dates:
        day=dt.date.fromisoformat(value)
        if day==target or abs((day-target).days)>14:raise ValueError('Dates must be within 14 days of target, excluding target day')
    return tuple(dates)

def classify(candidates,prior,entries,normalize,candidate_names):
    prior_index={r['record_id']:r for r in prior}
    by_name=defaultdict(list)
    for e in entries:by_name[normalize(e['name'])].append(e)
    output=[]
    for c in sorted(candidates,key=lambda x:x['record_id']):
        p=prior_index[c['record_id']]
        found={ (e['date'],e['event_id'],e['team'],e['espn_athlete_id']):e for n in candidate_names(c) for e in by_name.get(n,[])}
        matched=list(found.values());teams={e['team'] for e in matched};ids={e['espn_athlete_id'] for e in matched}
        report_team=c['report_team'].upper()
        if not matched:cls='NO_ADJACENT_BOX_SCORE_LISTING'
        elif len(ids)>1:cls='AMBIGUOUS_ESPN_IDENTITIES_REVIEW'
        elif report_team in teams and len(teams)>1:cls='CONFLICTING_ADJACENT_TEAM_LISTINGS_REVIEW'
        elif report_team in teams:cls='ADJACENT_SAME_TEAM_LISTING_UNCERTIFIED'
        else:cls='ADJACENT_OTHER_TEAM_LISTING_REVIEW'
        output.append({'record_id':c['record_id'],'raw_name':c['raw_name'],'candidate_nba_person_id':c['candidate_nba_person_id'],'report_team':report_team,'target_day_classification':p['classification'],'adjacent_classification':cls,'adjacent_dates':';'.join(sorted({e['date'] for e in matched})),'adjacent_teams':';'.join(sorted(teams)),'matching_espn_athlete_ids':';'.join(sorted(ids)),'evidence_ids':';'.join(sorted({'ESPN_SUMMARY_'+e['date'].replace('-','')+'_'+e['event_id'] for e in matched})),'historical_team_verified':'NO','training_decision':'BLOCK_TRAINING'})
    return output

def csv_data(rows):
    b=io.StringIO(newline='');w=csv.DictWriter(b,fieldnames=FIELDS,lineterminator='\n');w.writeheader();w.writerows(rows);return b.getvalue().encode('utf-8')

def fetch(url,timeout):
    req=urllib.request.Request(url,headers={'User-Agent':'NBA_MIKE_v2 research/1.0','Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        if r.status!=200:raise ValueError('Unexpected HTTP response '+str(r.status))
        raw=r.read(8_000_001)
    if len(raw)>8_000_000:raise ValueError('Oversized ESPN response')
    obj=json.loads(raw)
    if not isinstance(obj,dict):raise ValueError('Malformed ESPN JSON root')
    return obj,raw

def run(root,dates=DEFAULT_DATES,timeout=20,max_events=60):
    root=Path(root).resolve();dates=validate_dates(dates)
    s824=load_s824_module(root)
    predecessor,pre,prior,candidates=load_predecessor(root)
    captures={};entries=[];events=[]
    for date in dates:
        compact=date.replace('-','');url=API+'/scoreboard?dates='+compact
        board,raw=fetch(url,timeout);ids=s824.event_ids(board)
        if len(ids)>20:raise ValueError('Too many events on '+date)
        captures['scoreboard_'+compact]=(url,raw)
        for eid in ids:
            events.append((date,eid))
            if len(events)>max_events:raise ValueError('Event limit exceeded')
            summary_url=API+'/summary?event='+eid
            summary,blob=fetch(summary_url,timeout)
            header_id=str((summary.get('header') or {}).get('id') or '')
            if header_id and header_id!=eid:raise ValueError('ESPN summary event mismatch')
            label='summary_'+compact+'_'+eid
            captures[label]=(summary_url,blob)
            for item in s824.boxscore_entries(summary,eid):
                item['date']=date;entries.append(item)
    if not entries:raise ValueError('No adjacent-game listings retrieved')
    rows=classify(candidates,prior,entries,s824.normalize,s824.candidate_names)
    token=digest(b''.join(blob for _,blob in (captures[k] for k in sorted(captures))))[:16]
    dest=root/'research/p0_s8/s8_22_10_25/results'/TARGET/token
    dest.mkdir(parents=True,exist_ok=True)
    documents=[]
    for label,(url,raw) in sorted(captures.items()):
        filename=label+'.json';immutable(dest/filename,raw)
        documents.append({'source_url':url,'relative_path':filename,'sha256':digest(raw),'source_class':'THIRD_PARTY_ESPN_ADJACENT_GAME','retrieved_at_utc':dt.datetime.now(dt.timezone.utc).isoformat()})
    listings=encode(entries);review=csv_data(rows)
    immutable(dest/'adjacent_boxscore_listings.json',listings)
    immutable(dest/'adjacent_team_review.csv',review)
    counts=dict(sorted(Counter(r['adjacent_classification'] for r in rows).items()))
    report={'milestone':'S8.22.10.25','target_game_date':TARGET,'adjacent_dates':list(dates),'predecessor_report':str(predecessor.relative_to(root)),'predecessor_review_sha256':pre['review_csv_sha256'],'games_acquired':len(events),'raw_adjacent_listings':len(entries),'candidate_count':44,'target_day_missing_baseline':35,'classification_counts':counts,'source_class':'THIRD_PARTY_ESPN_ADJACENT_GAME','evidence_documents':documents,'adjacent_boxscore_listings_sha256':digest(listings),'adjacent_team_review_sha256':digest(review),'historical_team_verified':0,'player_ids_certified':0,'injury_statuses_certified':0,'historical_asof_certified':0,'research_status':'RESEARCH_ONLY','training_decision':'BLOCK_TRAINING','note':'Adjacent-day boxscore listings are retrospective leads only. They do not prove roster membership on 2023-11-15, absence, contracts, NBA-ID mapping, injury status or publication-time knowledge.'}
    report_path=dest/'review.json'
    if report_path.exists():
        existing=json.loads(report_path.read_text(encoding='utf-8'))
        for k in ('adjacent_dates','classification_counts','adjacent_team_review_sha256','adjacent_boxscore_listings_sha256'):
            if existing.get(k)!=report[k]:raise ValueError('Existing report conflict: '+k)
    else:immutable(report_path,encode(report))
    print('REPORT:',report_path)
    print(json.dumps({k:v for k,v in report.items() if k!='evidence_documents'},indent=2))
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');p.add_argument('--dates',nargs='+',default=list(DEFAULT_DATES));p.add_argument('--timeout',type=int,default=20);p.add_argument('--max-events',type=int,default=60)
    a=p.parse_args()
    try:run(a.project_root,a.dates,a.timeout,a.max_events)
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError,TimeoutError,ConnectionError) as e:p.exit(2,'FAIL CLOSED: '+str(e)+'\n')
if __name__=='__main__':main()
