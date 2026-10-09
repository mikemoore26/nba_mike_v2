"""S8.22.6 official NBA opening-night comparison, research-only."""
import argparse,csv,hashlib,json
from datetime import datetime,timezone
from pathlib import Path

EXPECTED={'2023-10-24':{
 '0022300061':('DEN','LAL','2023-10-24T23:30:00Z'),
 '0022300062':('GSW','PHX','2023-10-25T02:00:00Z')}}
SOURCES={
 'announcement':'https://www.nba.com/news/2023-24-nba-regular-season-schedule',
 'game_61':'https://www.nba.com/game/lal-vs-den-0022300061',
 'game_62':'https://www.nba.com/game/phx-vs-gsw-0022300062'}
FIELDS=['provider','provider_game_id','official_nba_game_id','game_date','home_provider_team_id','away_provider_team_id','tipoff_utc','tipoff_status','game_status']

def read_csv(path,required):
 with Path(path).open(newline='',encoding='utf-8-sig') as f:
  r=csv.DictReader(f)
  if not r.fieldnames or not set(required).issubset(r.fieldnames):raise ValueError('MISSING_COLUMNS')
  return list(r)

def utc(s):
 try:
  d=datetime.fromisoformat(s.replace('Z','+00:00'))
  return d.astimezone(timezone.utc) if d.tzinfo else None
 except (ValueError,AttributeError):return None

def run(provider_path,map_path,date):
 if date not in EXPECTED:raise ValueError('UNSUPPORTED_REFERENCE_DATE')
 raw=Path(provider_path).read_bytes(); games=read_csv(provider_path,FIELDS)
 if any(g['game_date']!=date for g in games):raise ValueError('OTHER_DATE_ROWS_FAIL_CLOSED')
 mapping=read_csv(map_path,['provider_team_id','official_team','evidence_url','reviewed_by'])
 mp={}
 for r in mapping:
  pid=r['provider_team_id'].strip(); abbr=r['official_team'].strip().upper()
  if not pid or not abbr or pid in mp:raise ValueError('INVALID_CROSSWALK')
  if abbr not in {'DEN','LAL','GSW','PHX'}:raise ValueError('INVALID_OFFICIAL_TEAM')
  mp[pid]=r
 ref=EXPECTED[date]; seen=set(); rows=[]
 for g in games:
  pid=g['provider_game_id'].strip()
  if not pid or pid in seen:raise ValueError('DUPLICATE_OR_EMPTY_PROVIDER_GAME_ID')
  seen.add(pid)
  h=mp.get(g['home_provider_team_id'].strip());a=mp.get(g['away_provider_team_id'].strip())
  matches=[(oid,v) for oid,v in ref.items() if h and a and (h['official_team'].upper(),a['official_team'].upper())==v[:2]]
  if len(matches)>1:raise ValueError('AMBIGUOUS_MATCH')
  oid,v=matches[0] if matches else ('',None)
  ptime=utc(g['tipoff_utc']);otime=utc(v[2]) if v else None
  diff=round(abs((ptime-otime).total_seconds())/60,2) if ptime and otime else None
  crosswalk_review=bool(h and a and h['evidence_url'].strip() and a['evidence_url'].strip() and h['reviewed_by'].strip() and a['reviewed_by'].strip())
  status=('UNMAPPED_TEAM' if not h or not a else 'NO_OFFICIAL_MATCH' if not oid else 'TIPOFF_MISSING_OR_INVALID' if diff is None else 'TIPOFF_DISAGREES' if diff>5 else 'CANDIDATE_MATCH_REVIEW_REQUIRED')
  rows.append(dict(provider_game_id=pid,official_nba_game_id_candidate=oid,home_team=h['official_team'] if h else '',away_team=a['official_team'] if a else '',tipoff_difference_minutes=diff if diff is not None else '',crosswalk_evidence_present=crosswalk_review,match_status=status))
 found=[r['official_nba_game_id_candidate'] for r in rows if r['official_nba_game_id_candidate']]
 if len(set(found))!=len(found):raise ValueError('DUPLICATE_OFFICIAL_CANDIDATE')
 coverage=len(rows)==len(ref)==len(found) and all(r['match_status']=='CANDIDATE_MATCH_REVIEW_REQUIRED' for r in rows)
 report=dict(milestone='S8.22.6',mode='OFFLINE_OFFICIAL_REFERENCE_CROSS_VALIDATION',requested_date=date,provider_rows=len(rows),official_reference_rows=len(ref),matched_candidates=len(found),missing_official_games=sorted(set(ref)-set(found)),unmatched_provider_rows=len(rows)-len(found),candidate_date_coverage='MATCH_REQUIRES_REVIEW' if coverage else 'INCOMPLETE_OR_UNVERIFIED',source_urls=SOURCES,reference_kind='NBA official publication and game pages; curated reference, not raw independently timestamped acquisition',reference_publication_date='2023-08-17',provider_csv_sha256=hashlib.sha256(raw).hexdigest(),provider_crosswalk='CANDIDATE_ONLY',tipoff_accuracy='CANDIDATE_ONLY',historical_asof_availability='NOT_CERTIFIED',future_schedule_approval='NOT_GRANTED',player_eligibility_verified=False,training_eligible=False,status='RESEARCH_ONLY',decision='BLOCK_TRAINING',limitations=['No live network requests by this script','Official reference is curated from publicly accessible NBA pages; not archived source bytes','Crosswalk must be independently documented and reviewed','One date cannot establish general schedule coverage','No training or production schedule approval'])
 return report,rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--project-root',type=Path,default=Path('.'));p.add_argument('--date',default='2023-10-24');p.add_argument('--provider-csv',type=Path);p.add_argument('--team-map-csv',type=Path);a=p.parse_args()
 root=a.project_root.resolve();base=root/'research/p0_s8/s8_22_6';base.mkdir(parents=True,exist_ok=True)
 provider=a.provider_csv or root/'research/p0_s8/s8_22_4/results/s8_22_4_games.csv'
 teammap=a.team_map_csv or base/'team_crosswalk_review.csv'
 report,rows=run(provider,teammap,a.date);out=base/'results';out.mkdir(exist_ok=True)
 (out/'s8_22_6_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 with (out/'s8_22_6_comparison.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=['provider_game_id','official_nba_game_id_candidate','home_team','away_team','tipoff_difference_minutes','crosswalk_evidence_present','match_status']);w.writeheader();w.writerows(rows)
 print(json.dumps({k:report[k] for k in ('provider_rows','matched_candidates','candidate_date_coverage','decision')},indent=2))
if __name__=='__main__':main()
