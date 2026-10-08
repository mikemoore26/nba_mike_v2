"""S7.31: independently source-backed origin evidence review, never roster promotion."""
import argparse,csv,hashlib,json,re,unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import quote

TEAM=set('ATL BOS BKN CHA CHI CLE DAL DEN DET GSW HOU IND LAC LAL MEM MIA MIL MIN NOP NYK OKC ORL PHI PHX POR SAC SAS TOR UTA WAS'.split())
FIELDS=['candidate_number','player_name','player_id','event_date','to_team','reported_from_team','proposed_from_team','review_status','reason','independent_source_url','independent_sha256','source_excerpt','discovery_url']
EVIDENCE=['candidate_number','player_id','event_date','from_team','to_team','source_url','snapshot_path','snapshot_sha256','verbatim_excerpt']

def norm(s):
 s=unicodedata.normalize('NFKD',s.replace('’',"'"))
 return re.sub(r'[^a-z0-9]','', ''.join(c for c in s if not unicodedata.combining(c)).lower())

def load(path,needed):
 with Path(path).open(newline='',encoding='utf-8-sig') as f:
  reader=csv.DictReader(f)
  if not reader.fieldnames or not needed.issubset(reader.fieldnames):raise ValueError('CSV schema missing required fields: '+str(path))
  return list(reader)

def verify(snapshot,sha,excerpt,player):
 p=Path(snapshot)
 if not p.is_file():return 'SNAPSHOT_NOT_FOUND'
 raw=p.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=sha:return 'SNAPSHOT_SHA_MISMATCH'
 text=raw.decode('utf-8',errors='replace')
 if not excerpt.strip() or excerpt not in text:return 'EXCERPT_NOT_IN_SOURCE'
 if norm(player) not in norm(excerpt):return 'PLAYER_NOT_IN_EXCERPT'
 return 'EXCERPT_LOCATED'

def audit(review_csv,evidence_csv,out_dir,source_sha=None):
 rows=load(review_csv,{'candidate_number','player_name','player_id','event_date','to_team','from_team','source_sha256','validation_flags'})
 if not rows:raise ValueError('Empty S7.30 review')
 shas={r['source_sha256'] for r in rows}
 if len(shas)!=1 or not re.fullmatch('[0-9a-f]{64}',next(iter(shas))):raise ValueError('Invalid source provenance')
 if source_sha and next(iter(shas))!=source_sha:raise ValueError('S7.30 source SHA mismatch')
 ids=[r['candidate_number'] for r in rows]
 if len(ids)!=len(set(ids)):raise ValueError('Duplicate candidate IDs')
 evidence=load(evidence_csv,set(EVIDENCE));group={}
 for e in evidence:
  if e['candidate_number'] not in ids:raise ValueError('Unknown evidence candidate number')
  group.setdefault(e['candidate_number'],[]).append(e)
 output=[];counts=Counter()
 for r in rows:
  flags=set(r['validation_flags'].split(';'));key=r['candidate_number'];matches=[];errors=[]
  for e in group.get(key,[]):
   if any(e[k]!=r[k] for k in ('player_id','event_date','to_team')):errors.append('CANDIDATE_FIELDS_MISMATCH');continue
   if not r['player_id'].isdigit():errors.append('UNRESOLVED_IDENTITY');continue
   if e['from_team'] not in TEAM or e['from_team']==r['to_team']:errors.append('INVALID_ORIGIN');continue
   if not e['source_url'].startswith('https://') or 'nba.com/news/2025-26-nba-trade-tracker' in e['source_url']:errors.append('NOT_INDEPENDENT_URL');continue
   if not re.fullmatch('[0-9a-f]{64}',e['snapshot_sha256']):errors.append('INVALID_SNAPSHOT_HASH');continue
   check=verify(e['snapshot_path'],e['snapshot_sha256'],e['verbatim_excerpt'],r['player_name'])
   if check!='EXCERPT_LOCATED':errors.append(check);continue
   # An excerpt mentioning a player does NOT prove the teams or event date: source claims remain review-only.
   matches.append(e)
  origins={e['from_team'] for e in matches}
  if len(origins)>1:status='CONFLICTING_SOURCE_ASSERTIONS';reason='Different source assertions for origin'
  elif len(matches)>1:status='MULTIPLE_SOURCE_ASSERTIONS_REVIEW';reason='Multiple excerpts; manual team/date semantics still required'
  elif len(matches)==1:status='SOURCE_EXCERPT_LOCATED_REVIEW';reason='Excerpt located, but origin/date semantics not independently validated'
  elif errors:status='EVIDENCE_REJECTED';reason=';'.join(sorted(set(errors)))
  else:status='NO_INDEPENDENT_EVIDENCE';reason='No independent source excerpt supplied'
  if 'MULTIPLE_DESTINATIONS_SAME_DAY' in flags:reason+=';MULTI_DESTINATION_REVIEW'
  if r['from_team'] and origins and r['from_team'] not in origins:reason+=';ORIGIN_DISAGREES_WITH_S728'
  e=matches[0] if len(matches)==1 else None
  output.append(dict(candidate_number=key,player_name=r['player_name'],player_id=r['player_id'],event_date=r['event_date'],to_team=r['to_team'],reported_from_team=r['from_team'],proposed_from_team=next(iter(origins)) if len(origins)==1 else '',review_status=status,reason=reason,independent_source_url=e['source_url'] if e else '',independent_sha256=e['snapshot_sha256'] if e else '',source_excerpt=e['verbatim_excerpt'] if e else '',discovery_url='https://www.nba.com/search?query='+quote(r['player_name']+' trade 2026')))
  counts[status]+=1
 out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
 with (out/'s7_31_review.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(output)
 report=dict(milestone='S7.31',status='RESEARCH_ONLY',decision='BLOCK_TRAINING',input_candidates=len(rows),independent_evidence_rows=len(evidence),source_excerpt_located_review=counts['SOURCE_EXCERPT_LOCATED_REVIEW'],multiple_source_assertions_review=counts['MULTIPLE_SOURCE_ASSERTIONS_REVIEW'],conflicting_source_assertions=counts['CONFLICTING_SOURCE_ASSERTIONS'],evidence_rejected=counts['EVIDENCE_REJECTED'],no_independent_evidence=counts['NO_INDEPENDENT_EVIDENCE'],missing_origin=sum(not r['from_team'] for r in rows),qualified_s726_events=0,verified_injury_assignments=0,historical_publication_verified=False,eligible_for_asof_training=False,limitations=['Source excerpt match does not authenticate transaction origin, date, trade participation, or historical publication time','Source URLs are user supplied and not independently authenticated by this script','No automatic promotion to S7.26/S7.23 or continuous roster intervals'])
 (out/'s7_31_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--review-csv',default='research/p0_s4/s7_30/results/s7_30_review.csv');p.add_argument('--evidence-csv',default='research/p0_s4/s7_31/independent_evidence.csv');p.add_argument('--output-dir',default='research/p0_s4/s7_31/results');a=p.parse_args()
 try:print(json.dumps(audit(a.review_csv,a.evidence_csv,a.output_dir),indent=2))
 except (OSError,ValueError,KeyError) as ex:
  print(json.dumps({'milestone':'S7.31','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(ex)}));raise SystemExit(1)
if __name__=='__main__':main()
