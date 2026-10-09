"""Offline, fail-closed multi-date provider/independent-reference audit. No API calls."""
import argparse,csv,hashlib,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

PROVIDER_COLUMNS={'provider_game_id','game_date','home_provider_team_id','away_provider_team_id','tipoff_utc'}
REFERENCE_COLUMNS={'game_date','official_nba_game_id','home_team','away_team','tipoff_utc','source_url','evidence_sha256','evidence_retrieved_utc'}
RESULT_COLUMNS=['date','status','provider_rows','reference_rows','matched_candidates','missing_official_games','unmatched_provider_games','duplicate_provider_ids','duplicate_reference_ids','tipoff_discrepancies','ambiguous_matches','missing_evidence','provider_sha256','reference_sha256']

def read_csv(path,required):
 with Path(path).open(newline='',encoding='utf-8-sig') as f:
  r=csv.DictReader(f)
  if not r.fieldnames or not required.issubset(r.fieldnames):raise ValueError('MISSING_COLUMNS: '+str(path))
  return list(r)

def timestamp(value):
 try:
  dt=datetime.fromisoformat(value.replace('Z','+00:00'))
  return dt.astimezone(timezone.utc) if dt.tzinfo else None
 except (ValueError,AttributeError):return None

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def audit_date(date,provider_path,reference_path,mapping,threshold=5):
 out=dict.fromkeys(RESULT_COLUMNS,'')
 out.update(date=date,status='UNVERIFIED',provider_rows=0,reference_rows=0,matched_candidates=0,missing_official_games=0,unmatched_provider_games=0,duplicate_provider_ids=0,duplicate_reference_ids=0,tipoff_discrepancies=0,ambiguous_matches=0,missing_evidence=0)
 if not provider_path or not Path(provider_path).is_file():out['status']='PROVIDER_SNAPSHOT_MISSING';return out
 out['provider_sha256']=digest(provider_path)
 provider=read_csv(provider_path,PROVIDER_COLUMNS)
 if any(r['game_date']!=date for r in provider):out['status']='PROVIDER_DATE_MISMATCH';return out
 out['provider_rows']=len(provider)
 pids=[r['provider_game_id'].strip() for r in provider];out['duplicate_provider_ids']=sum(n-1 for n in Counter(pids).values() if n>1)+pids.count('')
 if not reference_path or not Path(reference_path).is_file():out['status']='INDEPENDENT_REFERENCE_MISSING';return out
 out['reference_sha256']=digest(reference_path)
 refs=read_csv(reference_path,REFERENCE_COLUMNS)
 if any(r['game_date']!=date for r in refs):out['status']='REFERENCE_DATE_MISMATCH';return out
 out['reference_rows']=len(refs)
 ids=[r['official_nba_game_id'].strip() for r in refs];out['duplicate_reference_ids']=sum(n-1 for n in Counter(ids).values() if n>1)+ids.count('')
 out['missing_evidence']=sum(not(r['source_url'].strip() and len(r['evidence_sha256'].strip())==64 and timestamp(r['evidence_retrieved_utc'])) for r in refs)
 if out['duplicate_provider_ids'] or out['duplicate_reference_ids']:
  out['status']='DUPLICATE_IDS';return out
 if not refs and not provider:
  # Empty reference files cannot prove a genuinely game-free day without explicit external evidence.
  out['status']='EMPTY_BOTH_UNVERIFIED';return out
 matches=[]; used=set()
 for p in provider:
  home=mapping.get(p['home_provider_team_id'].strip());away=mapping.get(p['away_provider_team_id'].strip())
  candidates=[(i,r) for i,r in enumerate(refs) if home and away and r['home_team'].strip().upper()==home and r['away_team'].strip().upper()==away]
  if len(candidates)>1:out['ambiguous_matches']+=1;continue
  if len(candidates)!=1:continue
  i,r=candidates[0]
  if i in used:out['ambiguous_matches']+=1;continue
  used.add(i);matches.append((p,r))
  pt=timestamp(p['tipoff_utc']);rt=timestamp(r['tipoff_utc'])
  if not pt or not rt or abs((pt-rt).total_seconds())>threshold*60:out['tipoff_discrepancies']+=1
 out['matched_candidates']=len(matches)
 out['missing_official_games']=len(refs)-len(used)
 out['unmatched_provider_games']=len(provider)-len(matches)
 if out['missing_evidence']:out['status']='REFERENCE_EVIDENCE_INCOMPLETE'
 elif out['ambiguous_matches']:out['status']='AMBIGUOUS_MATCHES'
 elif out['missing_official_games'] or out['unmatched_provider_games']:out['status']='COVERAGE_MISMATCH'
 elif out['tipoff_discrepancies']:out['status']='TIPOFF_DISCREPANCY'
 else:out['status']='CANDIDATE_MATCH_REVIEW_REQUIRED'
 return out

def run(manifest_path,crosswalk_path,root):
 manifest=read_csv(manifest_path,{'date','phase','provider_csv','reference_csv','selection_reason'})
 crosswalk=read_csv(crosswalk_path,{'provider_team_id','official_team','evidence_url','reviewed_by'})
 mapping={}
 for r in crosswalk:
  pid=r['provider_team_id'].strip();team=r['official_team'].strip().upper()
  if not pid or not team or pid in mapping or not r['evidence_url'].strip() or not r['reviewed_by'].strip():raise ValueError('INVALID_CROSSWALK')
  mapping[pid]=team
 dates=[];seen=set()
 for r in manifest:
  date=r['date'].strip()
  try:datetime.strptime(date,'%Y-%m-%d')
  except ValueError:raise ValueError('INVALID_DATE')
  if date in seen:raise ValueError('DUPLICATE_MANIFEST_DATE')
  seen.add(date)
  def safe_rel(s):
   if not s.strip():return None
   p=Path(s.strip())
   if p.is_absolute() or '..' in p.parts:raise ValueError('UNSAFE_MANIFEST_PATH')
   return root/p
  result=audit_date(date,safe_rel(r['provider_csv']),safe_rel(r['reference_csv']),mapping)
  result['phase']=r['phase'];result['selection_reason']=r['selection_reason'];dates.append(result)
 summary={'milestone':'S8.22.7','mode':'OFFLINE_MULTI_DATE_AUDIT','dates_requested':len(dates),'dates_with_candidate_matches':sum(r['status']=='CANDIDATE_MATCH_REVIEW_REQUIRED' for r in dates),'date_status_counts':dict(Counter(r['status'] for r in dates)),'independent_reference_provenance':'USER_SUPPLIED_UNVERIFIED','historical_asof_availability':'NOT_CERTIFIED','routine_collection_approved':False,'training_eligible':False,'status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','limitations':['Reference source URLs and SHA256 values require independent manual verification','Retrospective matches cannot prove pregame availability','No network requests, no model fitting, no provider approval','Blank reference is not proof of a no-game date']}
 return summary,dates

def main():
 p=argparse.ArgumentParser();p.add_argument('--project-root',type=Path,default=Path('.'));p.add_argument('--manifest',type=Path);p.add_argument('--crosswalk',type=Path);a=p.parse_args()
 root=a.project_root.resolve();base=root/'research/p0_s8/s8_22_7';manifest=a.manifest or base/'date_manifest.csv';crosswalk=a.crosswalk or root/'research/p0_s8/s8_22_6/team_crosswalk_review.csv'
 summary,rows=run(manifest,crosswalk,root);out=base/'results';out.mkdir(parents=True,exist_ok=True)
 (out/'s8_22_7_report.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
 with (out/'s8_22_7_date_audit.csv').open('w',newline='',encoding='utf-8') as f:
  fields=RESULT_COLUMNS+['phase','selection_reason'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
