#!/usr/bin/env python3
"""Offline, fail-closed NBA vs BALLDONTLIE team mapping comparison."""
import argparse,csv,hashlib,json,re,sys,uuid
from datetime import datetime,timezone
from pathlib import Path

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def utc(s):
 s=s.replace('Z','+00:00'); d=datetime.fromisoformat(s)
 if d.tzinfo is None:raise ValueError('Naive tipoff UTC')
 return d.astimezone(timezone.utc)
def compare(provider,official,crosswalk,receipt,expected_date):
 issues=[];matches=[];mapping={};seen=set(); evidence=set()
 if receipt.get('date')!=expected_date:issues.append('CAPTURE_DATE_MISMATCH')
 if receipt.get('provider_rows')!=len(provider):issues.append('CAPTURE_ROW_COUNT_MISMATCH')
 for c in crosswalk:
  tid=c.get('provider_team_id','').strip();abbr=c.get('nba_abbreviation','').strip();status=c.get('verification_status','').strip()
  if tid in mapping:issues.append('DUPLICATE_CROSSWALK_ID:'+tid)
  if not tid.isdigit() or not re.fullmatch('[A-Z]{3}',abbr):issues.append('BAD_CROSSWALK:'+tid)
  mapping[tid]=(abbr,status,c)
  if status=='VERIFIED_INDEPENDENT':
   if not c.get('evidence_url','').startswith('https://api.balldontlie.io/v1/teams') or not re.fullmatch('[a-f0-9]{64}',c.get('evidence_sha256','')) or not c.get('reviewed_by','').strip():issues.append('UNSUPPORTED_VERIFICATION:'+tid)
   else:evidence.add(tid)
  elif status!='CANDIDATE_INFERRED_FROM_MATCHUPS':issues.append('UNKNOWN_VERIFICATION_STATUS:'+tid)
 official_index={}
 for g in official:
  if g['official_nba_game_id'] in official_index:issues.append('DUPLICATE_OFFICIAL_ID')
  official_index[g['official_nba_game_id']]=g
 used=set()
 for p in provider:
  pid=p.get('provider_game_id','')
  if pid in seen:issues.append('DUPLICATE_PROVIDER_ID:'+pid)
  seen.add(pid)
  if p.get('game_date')!=expected_date:issues.append('PROVIDER_DATE_MISMATCH:'+pid)
  home=p.get('home_provider_team_id','');away=p.get('away_provider_team_id','')
  if home not in mapping or away not in mapping:
   issues.append('UNMAPPED_TEAM:'+pid);continue
  h=mapping[home][0];a=mapping[away][0]
  possible=[g for g in official if g['home_team']==h and g['away_team']==a]
  if len(possible)!=1:issues.append('MATCHUP_NOT_UNIQUE:'+pid);continue
  g=possible[0];gid=g['official_nba_game_id']
  if gid in used:issues.append('OFFICIAL_GAME_REUSED:'+gid)
  used.add(gid)
  try: delta=abs((utc(p['tipoff_utc'])-utc(g['tipoff_utc'])).total_seconds())/60
  except (ValueError,KeyError) as e:issues.append('INVALID_TIPOFF:'+pid);continue
  if delta>5:issues.append('TIPOFF_CONFLICT:'+pid)
  matches.append(dict(provider_game_id=pid,official_nba_game_id=gid,home_team=h,away_team=a,tipoff_delta_minutes=delta,team_evidence='VERIFIED_INDEPENDENT' if home in evidence and away in evidence else 'CANDIDATE'))
 for gid in official_index:
  if gid not in used:issues.append('OFFICIAL_UNMATCHED:'+gid)
 if len(provider)!=len(official):issues.append('COUNT_MISMATCH')
 all_verified=all(m['team_evidence']=='VERIFIED_INDEPENDENT' for m in matches) and bool(matches)
 status='CONFLICT' if issues else ('CANDIDATE_ALL_TEAMS_VERIFIED_METADATA_REVIEW_REQUIRED' if all_verified else 'CANDIDATE_TEAM_CROSSWALK_REVIEW_REQUIRED')
 return dict(milestone='S8.22.7.8',date=expected_date,provider_rows=len(provider),official_rows=len(official),matched_games=len(matches),matches=matches,issues=issues,crosswalk_independently_verified=all_verified,status=status,provider_agreement='CANDIDATE_ONLY' if not issues else 'CONFLICT',date_completeness='NOT_CERTIFIED',historical_asof='NOT_CERTIFIED',routine_collection_approved=False,training_eligible=False,decision='BLOCK_TRAINING',limitations=['A crosswalk status or evidence digest is metadata, not a verification of archived team-list bytes','Game-derived team mappings cannot serve as independent verification','The source was captured in 2026, not contemporaneously before 2023 tipoff','Date completeness and pregame population remain unverified'])
def main():
 a=argparse.ArgumentParser();a.add_argument('--project-root',default='.');a.add_argument('--date',default='2023-11-15');a.add_argument('--provider-csv',required=True);a.add_argument('--capture-report',required=True);a.add_argument('--official-report',required=True);a.add_argument('--crosswalk-csv',required=True);x=a.parse_args();root=Path(x.project_root).resolve()
 def local(s):
  p=Path(s);return p if p.is_absolute() else root/p
 p=local(x.provider_csv);r=local(x.capture_report);o=local(x.official_report);c=local(x.crosswalk_csv)
 for f in (p,r,o,c):
  if not f.is_file():a.error('Missing input: '+str(f))
 receipt=json.loads(r.read_text());off=json.loads(o.read_text()); issues=[]
 if receipt.get('provider_csv_sha256')!=digest(p):issues.append('PROVIDER_SHA256_MISMATCH')
 if receipt.get('parse_status')!='PASS' or receipt.get('http_status')!=200:issues.append('PROVIDER_CAPTURE_NOT_PASS')
 if off.get('date')!=x.date or off.get('official_source_integrity')!='PASS':issues.append('OFFICIAL_REPORT_NOT_VERIFIED')
 if off.get('official_game_count')!=len(off.get('official_games',[])):issues.append('OFFICIAL_ROW_COUNT_MISMATCH')
 result=compare(load_csv(p),off.get('official_games',[]),load_csv(c),receipt,x.date)
 result['issues']=issues+result['issues'];result['status']='CONFLICT' if result['issues'] else result['status']
 result['provider_snapshot_sha256']=digest(p);result['official_report_sha256']=digest(o);result['crosswalk_sha256']=digest(c)
 folder=root/'research/p0_s8/s8_22_7_8/results'/x.date;folder.mkdir(parents=True,exist_ok=True);out=folder/('comparison_'+uuid.uuid4().hex+'.json');out.write_text(json.dumps(result,indent=2)+'\n');print('REPORT:',out);print('MATCHES:',result['matched_games'],'ISSUES:',len(result['issues']));print('STATUS:',result['status']);print('DECISION: BLOCK_TRAINING');return 1 if result['issues'] else 0
if __name__=='__main__':sys.exit(main())
