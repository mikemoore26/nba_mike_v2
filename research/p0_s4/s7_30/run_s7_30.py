"""S7.30 cross-check identity and transaction structure, never certify transactions."""
import argparse,csv,hashlib,json,re
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

TEAMS=set('ATL BOS BKN CHA CHI CLE DAL DEN DET GSW HOU IND LAC LAL MEM MIA MIL MIN NOP NYK OKC ORL PHI PHX POR SAC SAS TOR UTA WAS'.split())
FIELDS=['candidate_number','event_date','player_name','player_id','to_team','from_team','identity_status','validation_status','validation_flags','source_sha256','directory_sha256','evidence_class']

def load_csv(path,required):
 with Path(path).open(encoding='utf-8-sig',newline='') as f:
  r=csv.DictReader(f)
  if not r.fieldnames or not required.issubset(r.fieldnames):raise ValueError(f'Invalid CSV schema: {path}')
  rows=list(r)
 if not rows:raise ValueError(f'Empty source rows: {path}')
 return rows

def audit(review_path,identity_path,source_html,output_dir):
 sha=hashlib.sha256(Path(source_html).read_bytes()).hexdigest()
 review=load_csv(review_path,{'candidate_number','player_name','event_date','to_team','from_team','source_sha256','review_reason'})
 identity=load_csv(identity_path,{'candidate_number','player_name','player_id','identity_status','event_date','to_team','from_team','source_sha256','directory_sha256'})
 if len(review)!=len(identity):raise ValueError('Candidate row counts disagree')
 by_id={}
 for r in identity:
  key=r['candidate_number']
  if key in by_id:raise ValueError('Duplicate identity candidate number')
  by_id[key]=r
 if len(set(r['candidate_number'] for r in review))!=len(review):raise ValueError('Duplicate review candidate number')
 if set(by_id)!={r['candidate_number'] for r in review}:raise ValueError('Candidate numbers disagree')
 directory_shas={r['directory_sha256'] for r in identity}
 if len(directory_shas)!=1 or not re.fullmatch(r'[0-9a-f]{64}',next(iter(directory_shas))):raise ValueError('Invalid directory provenance')
 out=[];groups=defaultdict(set);counts=Counter()
 for r in review:
  i=by_id[r['candidate_number']]
  for key in ('player_name','event_date','to_team','from_team','source_sha256'):
   if r[key]!=i[key]:raise ValueError(f'Candidate {r["candidate_number"]}: identity/review {key} mismatch')
  if r['source_sha256']!=sha:raise ValueError('Captured HTML SHA-256 mismatch')
  flags=[];pid=i['player_id'].strip();status=i['identity_status'];name=r['player_name'].strip()
  if 'NON_PLAYER_ASSET' in r['review_reason']:
   flags.append('NON_PLAYER_ASSET')
   if status!='NON_PLAYER_ASSET' or pid:raise ValueError('Non-player asset incorrectly assigned an identity')
  else:
   if status=='EXACT_UNIQUE_ID_CANDIDATE':
    if not pid.isdigit() or not name:raise ValueError('Invalid resolved identity')
   elif pid:raise ValueError('Unresolved identity has a player ID')
   else:flags.append('UNRESOLVED_PLAYER_ID')
  if not re.fullmatch(r'20\d\d-\d\d-\d\d',r['event_date']):flags.append('UNSUPPORTED_EVENT_DATE')
  if r['to_team'] not in TEAMS:flags.append('UNKNOWN_DESTINATION')
  if not r['from_team']:flags.append('ORIGIN_NOT_ESTABLISHED')
  elif r['from_team'] not in TEAMS:flags.append('UNKNOWN_ORIGIN')
  elif r['from_team']==r['to_team']:flags.append('SAME_TEAM_ORIGIN_DESTINATION')
  if pid and r['event_date'] and r['to_team'] in TEAMS:
   groups[(pid,r['event_date'])].add(r['to_team'])
  # Source page headings do not independently authenticate effective date or historical availability.
  flags.append('EVENT_DATE_AND_SOURCE_PUBLICATION_UNVERIFIED')
  out.append({'candidate_number':r['candidate_number'],'event_date':r['event_date'],'player_name':name,'player_id':pid,'to_team':r['to_team'],'from_team':r['from_team'],'identity_status':status,'validation_status':'REVIEW_REQUIRED','validation_flags':flags,'source_sha256':sha,'directory_sha256':i['directory_sha256'],'evidence_class':'TRANSACTION_CANDIDATE_ONLY'})
 for row in out:
  if row['player_id'] and len(groups[(row['player_id'],row['event_date'])])>1:
   row['validation_flags'].append('MULTIPLE_DESTINATIONS_SAME_DAY')
  for flag in row['validation_flags']:counts[flag]+=1
  row['validation_flags']=';'.join(row['validation_flags'])
 dest=Path(output_dir);dest.mkdir(parents=True,exist_ok=True)
 with (dest/'s7_30_review.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(out)
 report={'milestone':'S7.30','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','source_sha256':sha,'directory_sha256':next(iter(directory_shas)),'input_candidates':len(out),'identity_candidates':sum(r['identity_status']=='EXACT_UNIQUE_ID_CANDIDATE' for r in out),'unresolved_identities':counts['UNRESOLVED_PLAYER_ID'],'non_player_assets':counts['NON_PLAYER_ASSET'],'missing_origin':counts['ORIGIN_NOT_ESTABLISHED'],'multiple_destinations_same_day':sum('MULTIPLE_DESTINATIONS_SAME_DAY' in r['validation_flags'] for r in out),'same_team_origin_destination':counts['SAME_TEAM_ORIGIN_DESTINATION'],'review_required':len(out),'qualified_s726_events':0,'verified_injury_assignments':0,'historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['Same-day multiple destinations are review flags, not proof of contradictory trades; multi-team movements are possible','Transaction tracker section dates and original publication time remain unverified','NBA player ID matches do not authenticate transaction participation','No S7.26/S7.23 export or roster interval promotion']}
 (dest/'s7_30_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--review-csv',default='research/p0_s4/s7_28/results/s7_28_review.csv');p.add_argument('--identity-csv',default='research/p0_s4/s7_29/results/s7_29_identity_candidates.csv');p.add_argument('--source-html');p.add_argument('--output-dir',default='research/p0_s4/s7_30/results');a=p.parse_args()
 try:
  html=a.source_html
  if not html:
   matches=list(Path('research/p0_s4/s7_27/results/objects').glob('*.html'))
   if len(matches)!=1:raise ValueError('Specify --source-html when original HTML count is not exactly one')
   html=matches[0]
  print(json.dumps(audit(a.review_csv,a.identity_csv,html,a.output_dir),indent=2))
 except (ValueError,OSError,KeyError) as e:
  print(json.dumps({'milestone':'S7.30','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(e)}));raise SystemExit(1)
if __name__=='__main__':main()
