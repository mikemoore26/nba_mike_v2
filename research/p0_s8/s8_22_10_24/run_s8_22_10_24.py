"""S8.22.10.24: capture dated ESPN NBA boxscore evidence, without certifying rosters.

ESPN is an independent third-party source. Game-day boxscore listing is not a
transaction history, and absence from a boxscore is never negative roster proof.
"""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

DATE = '2023-11-15'
API = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba'
FIELDS = ['record_id','raw_name','candidate_nba_person_id','report_team','classification','matching_event_ids','matching_espn_athlete_ids','evidence_ids','historical_team_verified','training_decision']

def digest(b): return hashlib.sha256(b).hexdigest()
def encoded(obj): return (json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf-8')
def immutable(path,blob):
    if path.exists() and path.read_bytes()!=blob: raise ValueError('Immutable evidence conflict: '+str(path))
    if not path.exists(): path.write_bytes(blob)
def fetch(url,timeout=15):
    req=urllib.request.Request(url,headers={'User-Agent':'NBA_MIKE_v2 historical evidence research/1.0','Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        if r.status!=200: raise ValueError(f'HTTP {r.status}: {url}')
        body=r.read(8_000_001)
    if len(body)>8_000_000: raise ValueError('Oversized response')
    obj=json.loads(body)
    if not isinstance(obj,dict): raise ValueError('Unexpected JSON root')
    return obj,body

def event_ids(scoreboard):
    events=scoreboard.get('events')
    if not isinstance(events,list) or not events: raise ValueError('Missing scoreboard events')
    out=[]
    for e in events:
        eid=str(e.get('id',''))
        if not eid.isdigit(): raise ValueError('Malformed ESPN event ID')
        if not str(e.get('date','')).startswith(DATE):
            # UTC tipoff for evening games can fall on the following day.
            # Trust requested scoreboard slate rather than UTC date matching.
            pass
        out.append(eid)
    if len(set(out))!=len(out): raise ValueError('Duplicate scoreboard event ID')
    return sorted(out)

def boxscore_entries(summary,event_id):
    """Extract ESPN boxscore listings; don't equate listing with participation."""
    result=[]
    groups=summary.get('boxscore',{}).get('players',[])
    if not isinstance(groups,list): raise ValueError('Malformed boxscore groups')
    for g in groups:
        team=g.get('team',{})
        abbr=str(team.get('abbreviation','')).upper()
        if not abbr: continue
        for statgroup in g.get('statistics',[]):
            for entry in statgroup.get('athletes',[]):
                athlete=entry.get('athlete') or {}
                name=str(athlete.get('displayName') or athlete.get('fullName') or '').strip()
                aid=str(athlete.get('id',''))
                if not name or not aid.isdigit(): continue
                result.append({'event_id':event_id,'team':abbr,'name':name,'espn_athlete_id':aid,'did_not_play':bool(entry.get('didNotPlay',False)),'boxscore_listed':True})
    return result

def normalize(name):
    import unicodedata,re
    s=unicodedata.normalize('NFKD',name).casefold()
    s=''.join(c for c in s if not unicodedata.combining(c))
    s=re.sub(r'[^a-z0-9 ]',' ',s)
    return ' '.join(s.split())

def candidate_names(r):
    names={normalize(r['registry_full_name'])}
    raw=r['raw_name']
    if ',' in raw:
        last,first=raw.split(',',1)
        names.add(normalize(first+' '+last))
    else:names.add(normalize(raw))
    return names

def reconcile(candidates,entries):
    index=defaultdict(list)
    for entry in entries:index[normalize(entry['name'])].append(entry)
    results=[]
    for r in sorted(candidates,key=lambda x:x['record_id']):
        found={ (e['event_id'],e['espn_athlete_id'],e['team']):e for name in candidate_names(r) for e in index.get(name,[])}
        matches=list(found.values())
        same=[e for e in matches if e['team']==r['report_team'].upper()]
        other=[e for e in matches if e['team']!=r['report_team'].upper()]
        if same and other:cls='CONFLICTING_GAME_DAY_BOX_SCORE_LISTINGS'
        elif same:cls='SAME_TEAM_BOX_SCORE_LISTING_UNCERTIFIED'
        elif other:cls='OTHER_TEAM_BOX_SCORE_LISTING_REVIEW'
        else:cls='NO_BOX_SCORE_LISTING_NOT_NEGATIVE_PROOF'
        results.append({'record_id':r['record_id'],'raw_name':r['raw_name'],'candidate_nba_person_id':r['candidate_nba_person_id'],'report_team':r['report_team'],'classification':cls,'matching_event_ids':';'.join(sorted({e['event_id'] for e in matches})),'matching_espn_athlete_ids':';'.join(sorted({e['espn_athlete_id'] for e in matches})),'evidence_ids':';'.join(sorted({'ESPN_BOX_'+e['event_id'] for e in matches})),'historical_team_verified':'NO','training_decision':'BLOCK_TRAINING'})
    return results

def candidates_from(root):
    base=root/'research/p0_s8/s8_22_10_22a/results'/DATE
    matches=[]
    for mf in base.glob('*/capture_manifest.json'):
        m=json.loads(mf.read_text(encoding='utf-8'))
        csvpath=mf.parent/'player_id_candidates.csv'
        if m.get('milestone')=='S8.22.10.22A' and m.get('training_decision')=='BLOCK_TRAINING' and csvpath.is_file() and digest(csvpath.read_bytes())==m.get('candidate_csv_sha256'):
            matches.append((mf,csvpath,m))
    if len(matches)!=1:raise ValueError(f'Expected exactly one validated S8.22.10.22A capture; got {len(matches)}')
    mf,path,m=matches[0]
    with path.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    if len(rows)!=44 or len({r['record_id'] for r in rows})!=44:raise ValueError('Expected 44 unique candidates')
    for r in rows:
        if r.get('match_class')!='UNIQUE_NAME_ID_CANDIDATE' or not r.get('candidate_nba_person_id','').isdigit() or not r.get('report_team') or not r.get('registry_full_name') or r.get('historical_team_verified')!='NO':raise ValueError('Invalid candidate record')
    return rows,mf,m

def csv_blob(rows):
    out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=FIELDS,lineterminator='\n');w.writeheader();w.writerows(rows)
    return out.getvalue().encode('utf-8')

def run(root):
    root=Path(root).resolve();candidates,mf,pre=candidates_from(root)
    urls={'scoreboard':API+'/scoreboard?dates=20231115'}
    def get(label,url): return fetch(url)
    board,raw_board=get('scoreboard',urls['scoreboard']);ids=event_ids(board)
    if len(ids)>20:raise ValueError('Unexpectedly many scoreboard events')
    captures={'scoreboard':raw_board};entries=[]
    for eid in ids:
        label='summary_'+eid;url=API+'/summary?event='+eid;urls[label]=url
        summary,raw=get(label,url)
        # A returned event must be the event requested; fail if identity is present and differs.
        header_id=str((summary.get('header') or {}).get('id') or '')
        if header_id and header_id!=eid:raise ValueError('Summary event mismatch '+eid)
        captures[label]=raw;entries.extend(boxscore_entries(summary,eid))
    if not entries:raise ValueError('No ESPN boxscore player listings: cannot create useful evidence capture')
    rows=reconcile(candidates,entries)
    token=digest(raw_board+b''.join(captures[k] for k in sorted(captures) if k!='scoreboard'))[:16]
    dest=root/'research/p0_s8/s8_22_10_24/results'/DATE/token;dest.mkdir(parents=True,exist_ok=True)
    evidence=[]
    for label,blob in captures.items():
        filename=label+'.json';immutable(dest/filename,blob)
        evidence.append({'evidence_id':'ESPN_'+label.upper(),'source_url':urls[label],'relative_path':filename,'sha256':digest(blob),'captured_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_class':'THIRD_PARTY_ESPN_LIVE_RETRIEVAL'})
    entriesfile=dest/'boxscore_listings.json';immutable(entriesfile,encoded(entries))
    resultfile=dest/'historical_team_boxscore_review.csv';immutable(resultfile,csv_blob(rows))
    counts=dict(sorted(Counter(r['classification'] for r in rows).items()))
    report={'milestone':'S8.22.10.24','target_game_date':DATE,'source_class':'THIRD_PARTY_ESPN_GAME_DAY_BOX_SCORE','predecessor_manifest':str(mf.relative_to(root)),'predecessor_candidate_sha256':pre['candidate_csv_sha256'],'scoreboard_event_count':len(ids),'scoreboard_event_ids':ids,'raw_boxscore_listings':len(entries),'player_candidates':44,'classification_counts':counts,'evidence_documents':evidence,'boxscore_listings_sha256':digest(entriesfile.read_bytes()),'review_csv_sha256':digest(resultfile.read_bytes()),'historical_team_verified':0,'player_ids_certified':0,'injury_statuses_certified':0,'historical_asof_certified':0,'research_status':'RESEARCH_ONLY','training_decision':'BLOCK_TRAINING','note':'ESPN is third-party; boxscore listing supports game-day association only, not roster contracts, transactions, inactive-player absence or injury-report as-of certification.'}
    reportpath=dest/'review.json'
    if reportpath.exists():
        old=json.loads(reportpath.read_text(encoding='utf-8'))
        for k in ('scoreboard_event_ids','classification_counts','review_csv_sha256','boxscore_listings_sha256'):
            if old.get(k)!=report[k]:raise ValueError('Existing report conflict: '+k)
    else:reportpath.write_bytes(encoded(report))
    print('REPORT:',reportpath);print(json.dumps({k:v for k,v in report.items() if k!='evidence_documents'},indent=2));return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args()
    try:run(a.project_root)
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError,TimeoutError,ConnectionError) as e:p.exit(2,'FAIL CLOSED: '+str(e)+'\n')
if __name__=='__main__':main()
