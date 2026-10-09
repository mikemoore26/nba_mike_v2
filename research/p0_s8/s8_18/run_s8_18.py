"""S8.18: bounded alternate-source evidence inventory, never pregame certification."""
import argparse,csv,hashlib,json,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone

TIPOFF='2023-10-24T19:30:00-04:00'
SOURCES=[
 ('denver_team_preview','https://www.nba.com/nuggets/news/nuggets-open-regular-season-with-a-rematch-against-lakers','TEAM_EDITORIAL','2023-10-23T20:09:00-06:00','injury_status'),
 ('nba_opening_rosters','https://www.nba.com/news/nba-rosters-regular-season-2023-24','LEAGUE_OFFICIAL','2023-10-24T17:03:00-04:00','opening_roster'),
 ('nba_starting5','https://www.nba.com/news/starting-5-oct-24-2023','LEAGUE_EDITORIAL','2023-10-24T17:40:00-04:00','pregame_context'),
 ('yahoo_lebronwire','https://sports.yahoo.com/lakers-vs-nuggets-stream-lineups-160020959.html','THIRD_PARTY_SYNDICATED','2023-10-24','injury_and_projected_lineup'),
 ('nba_0630_report','https://ak-static.cms.nba.com/referee/injury/Injury-Report_2023-10-24_06PM.pdf','LEAGUE_OFFICIAL','2023-10-24T18:30:00-04:00','injury_status'),
 ('nba_postgame_box','https://www.nba.com/game/0022300061/box-score','POSTGAME','', 'outcome_only'),
]
FIELDS=['source_id','url','source_family','claimed_publication','claimed_before_tipoff','evidence_scope','retrieval_status','http_status','content_type','bytes','sha256','artifact_path','retrieved_utc','historical_capture_status','verdict','error']

def claimed_before(ts):
    try: return datetime.fromisoformat(ts)<datetime.fromisoformat(TIPOFF) if 'T' in ts else None
    except ValueError: return None

def fetch(url,timeout=12):
    req=urllib.request.Request(url,headers={'User-Agent':'NBA-MIKE-v2-research-evidence/0.1'})
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        data=resp.read(3_000_001)
        if len(data)>3_000_000: raise ValueError('SIZE_LIMIT_EXCEEDED')
        return data,resp.status,resp.headers.get('Content-Type','')

def audit(root,acquire=False):
    base=root/'research/p0_s8/s8_18'; results=base/'results'; artifacts=base/'artifacts'
    results.mkdir(parents=True,exist_ok=True); artifacts.mkdir(parents=True,exist_ok=True)
    rows=[]
    for sid,url,family,pub,scope in SOURCES:
        row=dict(source_id=sid,url=url,source_family=family,claimed_publication=pub,
          claimed_before_tipoff=str(claimed_before(pub)) if claimed_before(pub) is not None else 'UNKNOWN',
          evidence_scope=scope,retrieval_status='NOT_ATTEMPTED',http_status='',content_type='',bytes='',sha256='',
          artifact_path='',retrieved_utc='',historical_capture_status='NOT_OBTAINED',verdict='UNVERIFIED',error='')
        if family=='POSTGAME': row['verdict']='POST_TIPOFF_OUTCOME_ONLY'
        if acquire and family!='POSTGAME':
            try:
                data,status,ctype=fetch(url)
                ext='.pdf' if 'pdf' in ctype.lower() or url.lower().endswith('.pdf') else '.html'
                sha=hashlib.sha256(data).hexdigest(); path=artifacts/(sid+'_'+sha[:12]+ext)
                if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()!=sha: raise ValueError('EXISTING_ARTIFACT_HASH_MISMATCH')
                if not path.exists(): path.write_bytes(data)
                row.update(retrieval_status='ACQUIRED_CURRENT',http_status=status,content_type=ctype,bytes=len(data),sha256=sha,
                  artifact_path=str(path.relative_to(root)),retrieved_utc=datetime.now(timezone.utc).isoformat())
            except Exception as exc: row.update(retrieval_status='REQUEST_FAILED',error=f'{type(exc).__name__}: {exc}'[:350])
        rows.append(row)
    with (results/'s8_18_source_audit.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
    report={'milestone':'S8.18','mode':'ALTERNATIVE_HISTORICAL_EVIDENCE_SOURCE_INVESTIGATION',
      'game_id':'0022300061','scheduled_tipoff_et':TIPOFF,'network_opt_in':acquire,
      'source_candidates':len(rows),'current_artifacts_acquired':sum(r['retrieval_status']=='ACQUIRED_CURRENT' for r in rows),
      'historical_captures_verified':0,'independently_verified_games':0,
      'source_families':sorted(set(r['source_family'] for r in rows)),
      'decision':'BLOCK_TRAINING','status':'RESEARCH_ONLY','outcome':'ALTERNATIVE_SOURCES_IDENTIFIED_NOT_ASOF_CERTIFIED',
      'limitations':['Publisher date labels and present-day retrievals do not independently prove pregame public availability',
      'Denver Nuggets editorial and NBA.com share league affiliation; not fully independent sources',
      'Syndicated Yahoo/LeBron Wire may repeat league/team claims rather than independently establish availability',
      'Official rosters are not complete game-specific eligible player populations',
      'Postgame inactive lists and box scores must never be treated as pregame features',
      'No historical archive replay or independent capture timestamp established',
      'No training, model fitting, betting, or certification; 88 restart games remain blocked']}
    (results/'s8_18_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(results/'s8_18_report.json'),'acquired':report['current_artifacts_acquired'],'decision':report['decision']},indent=2))
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');p.add_argument('--acquire-sources',action='store_true');args=p.parse_args()
    audit(Path(args.project_root).resolve(),args.acquire_sources)
if __name__=='__main__': main()
