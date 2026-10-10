"""S8.22.7.5 offline multi-date coverage audit; never certifies training."""
import argparse,csv,hashlib,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4

DATES=("2023-10-24","2023-11-15","2024-01-15","2024-06-20","2026-10-10")
FIELDS=("date","phase","provider_csv","official_reference_csv","announcement_report_json","date_receipt_json","reviewed_date_csv","negative_evidence_receipt_json","reviewer_note")
PROVIDER={"provider_game_id","game_date","home_provider_team_id","away_provider_team_id","tipoff_utc"}
REFERENCE={"game_date","official_nba_game_id","home_team","away_team","tipoff_utc","source_url","evidence_sha256","evidence_retrieved_utc"}

def csv_rows(path,columns):
 with path.open(newline="",encoding="utf-8-sig") as f:
  reader=csv.DictReader(f)
  if not reader.fieldnames or not columns.issubset(reader.fieldnames):raise ValueError("MISSING_COLUMNS: "+str(path))
  return list(reader)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def utc(s):
 try:
  d=datetime.fromisoformat(str(s).replace("Z","+00:00"))
  return d.astimezone(timezone.utc) if d.tzinfo else None
 except (ValueError,TypeError,OverflowError):return None

def resolve(root,s):
 if not s or not s.strip():return None
 p=Path(s.strip())
 if p.is_absolute() or '..' in p.parts:raise ValueError('UNSAFE_PATH')
 result=(root/p).resolve()
 if not result.is_relative_to(root):raise ValueError('UNSAFE_PATH')
 return result

def valid_receipt(root,path,date):
 if not path or not path.is_file():return False,'RECEIPT_MISSING'
 try:
  receipt=json.loads(path.read_text(encoding='utf-8'))
  source=resolve(root,receipt.get('evidence_path',''))
  if not source or not source.is_file():return False,'SOURCE_BYTES_MISSING'
  if receipt.get('date')!=date:return False,'RECEIPT_DATE_MISMATCH'
  if not str(receipt.get('source_url','')).startswith('https://www.nba.com/'):return False,'NON_OFFICIAL_SOURCE'
  if sha(source)!=receipt.get('sha256') or source.stat().st_size!=receipt.get('bytes'):return False,'SOURCE_HASH_OR_SIZE_MISMATCH'
  if not utc(receipt.get('retrieved_utc')):return False,'RETRIEVAL_TIME_INVALID'
  return True,'SOURCE_INTEGRITY_PASS'
 except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as e:return False,'RECEIPT_INVALID'

def audit(root,manifest,crosswalk):
 mapping={}
 for row in csv_rows(crosswalk,{'provider_team_id','official_team','evidence_url','reviewed_by'}):
  pid=row['provider_team_id'].strip();team=row['official_team'].strip().upper()
  if not pid or pid in mapping or not team or not row['evidence_url'].strip() or not row['reviewed_by'].strip():raise ValueError('INVALID_CROSSWALK')
  mapping[pid]=team
 items=csv_rows(manifest,set(FIELDS)); seen=set();output=[]
 for item in items:
  date=item['date'].strip()
  if date not in DATES or date in seen:raise ValueError('INVALID_OR_DUPLICATE_DATE: '+date)
  seen.add(date)
  result={'date':date,'phase':item['phase'],'provider_rows':None,'official_reference_rows':None,'provider_snapshot_sha256':None,'official_reference_sha256':None,'matched_games':0,'missing_official_games':None,'unmatched_provider_games':None,'tipoff_conflicts':0,'source_issues':[],'status':'UNVERIFIED','date_completeness':'NOT_CERTIFIED','historical_asof':'NOT_CERTIFIED','training_eligible':False,'decision':'BLOCK_TRAINING'}
  def path(field):return resolve(root,item[field])
  pp=path('provider_csv');rp=path('official_reference_csv');ap=path('announcement_report_json');dr=path('date_receipt_json');rev=path('reviewed_date_csv');neg=path('negative_evidence_receipt_json')
  if not pp or not pp.is_file():result['status']='PROVIDER_SNAPSHOT_MISSING';output.append(result);continue
  p=csv_rows(pp,PROVIDER);result['provider_rows']=len(p);result['provider_snapshot_sha256']=sha(pp)
  if any(x['game_date'].strip()!=date for x in p):result['status']='PROVIDER_DATE_MISMATCH';output.append(result);continue
  pids=[x['provider_game_id'].strip() for x in p]
  if len(set(pids))!=len(pids) or any(not x for x in pids):result['status']='PROVIDER_DUPLICATE_IDS';output.append(result);continue
  if not p:
   if neg:
    ok,why=valid_receipt(root,neg,date);result['source_issues'].append('NEGATIVE_EVIDENCE_'+why)
   result['status']='ZERO_PROVIDER_ROWS_NEGATIVE_EVIDENCE_REVIEW_REQUIRED'
   result['source_issues'].append('A zero-row provider snapshot is not proof of a no-game date; manual negative evidence and date coverage review required')
   output.append(result);continue
  if not rp or not rp.is_file():result['status']='INDEPENDENT_REFERENCE_MISSING';output.append(result);continue
  refs=csv_rows(rp,REFERENCE);result['official_reference_rows']=len(refs);result['official_reference_sha256']=sha(rp)
  if not refs:result['status']='EMPTY_REFERENCE_UNVERIFIED';output.append(result);continue
  if any(x['game_date'].strip()!=date for x in refs):result['status']='REFERENCE_DATE_MISMATCH';output.append(result);continue
  ids=[x['official_nba_game_id'].strip() for x in refs]
  if len(set(ids))!=len(ids) or any(not x for x in ids):result['status']='REFERENCE_DUPLICATE_IDS';output.append(result);continue
  if any(not x['source_url'].startswith('https://www.nba.com/') or len(x['evidence_sha256'].strip())!=64 or not utc(x['evidence_retrieved_utc']) for x in refs):
   result['status']='REFERENCE_PROVENANCE_INCOMPLETE';output.append(result);continue
  used=set();matched=0
  for row in p:
   h=mapping.get(row['home_provider_team_id'].strip());a=mapping.get(row['away_provider_team_id'].strip())
   candidates=[i for i,x in enumerate(refs) if h and a and x['home_team'].strip().upper()==h and x['away_team'].strip().upper()==a]
   if len(candidates)!=1 or candidates[0] in used:
    result['source_issues'].append('UNMATCHED_OR_AMBIGUOUS_PROVIDER_GAME_'+row['provider_game_id']);continue
   i=candidates[0];used.add(i);matched+=1
   pt=utc(row['tipoff_utc']);rt=utc(refs[i]['tipoff_utc'])
   if not pt or not rt or abs((pt-rt).total_seconds())>300:result['tipoff_conflicts']+=1
  result['matched_games']=matched;result['missing_official_games']=len(refs)-len(used);result['unmatched_provider_games']=len(p)-matched
  if result['missing_official_games'] or result['unmatched_provider_games'] or result['tipoff_conflicts']:
   result['status']='PROVIDER_REFERENCE_CONFLICT';output.append(result);continue
  if ap and not ap.is_file():
   result['status']='ANNOUNCEMENT_REPORT_MISSING';output.append(result);continue
  if ap and ap.is_file():
   try:
    a=json.loads(ap.read_text(encoding='utf-8'))
    if a.get('date')==date and a.get('row_set_agreement') is True and a.get('announcement_rows')==len(refs) and a.get('game_reference_rows')==len(refs) and not a.get('conflicts') and not a.get('unsupported_quotes') and a.get('coverage_quote_present') is True and a.get('decision')=='BLOCK_TRAINING':
     result['status']='CANDIDATE_ANNOUNCEMENT_AGREEMENT_REVIEW_REQUIRED'
    else:result['status']='ANNOUNCEMENT_REPORT_CONFLICT'
   except (OSError,ValueError,TypeError):result['status']='ANNOUNCEMENT_REPORT_INVALID'
  elif dr or rev:
   if not dr or not rev or not rev.is_file():result['status']='DATE_LEVEL_REVIEW_INPUT_INCOMPLETE'
   else:
    ok,why=valid_receipt(root,dr,date)
    if not ok:result['status']='DATE_LEVEL_'+why
    else:
     reviewed=csv_rows(rev,{'game_date','official_nba_game_id','home_team','away_team','tipoff_utc'})
     if len(reviewed)!=len(refs) or set(x['official_nba_game_id'] for x in reviewed)!=set(ids):result['status']='DATE_LEVEL_ROW_SET_CONFLICT'
     else:
      lookup={x['official_nba_game_id']:x for x in refs}
      bad=any(x['game_date']!=date or x['home_team'].upper()!=lookup[x['official_nba_game_id']]['home_team'].upper() or x['away_team'].upper()!=lookup[x['official_nba_game_id']]['away_team'].upper() or not utc(x['tipoff_utc']) or abs((utc(x['tipoff_utc'])-utc(lookup[x['official_nba_game_id']]['tipoff_utc'])).total_seconds())>300 for x in reviewed)
      result['status']='DATE_LEVEL_ROW_CONFLICT' if bad else 'CANDIDATE_DATE_LEVEL_ROW_AGREEMENT_REVIEW_REQUIRED'
  else:result['status']='CANDIDATE_PROVIDER_GAME_MATCH_DATE_COVERAGE_MISSING'
  output.append(result)
 for date in DATES:
  if date not in seen:output.append({'date':date,'status':'MANIFEST_DATE_MISSING','date_completeness':'NOT_CERTIFIED','historical_asof':'NOT_CERTIFIED','training_eligible':False,'decision':'BLOCK_TRAINING'})
 output.sort(key=lambda x:x['date'])
 summary={'milestone':'S8.22.7.5','mode':'OFFLINE_COVERAGE_EXPANSION','date_count':len(output),'status_counts':dict(Counter(x['status'] for x in output)),'date_completeness':'NOT_CERTIFIED','historical_asof':'NOT_CERTIFIED','routine_collection_approved':False,'training_eligible':False,'decision':'BLOCK_TRAINING','limitations':['Snapshot presence is not schedule completeness','Reference URL and digest metadata do not verify underlying evidence bytes','An announcement agreement report is a candidate only and still requires human review','No-game and preseason dates require independent negative/date-coverage evidence','No network, no provider approval, no training']}
 return summary,output

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--project-root',type=Path,default=Path('.'));parser.add_argument('--manifest',type=Path);parser.add_argument('--crosswalk',type=Path);args=parser.parse_args()
 root=args.project_root.resolve();base=root/'research/p0_s8/s8_22_7_5';manifest=args.manifest or base/'coverage_manifest.csv';crosswalk=args.crosswalk or root/'research/p0_s8/s8_22_6/team_crosswalk_review.csv'
 summary,rows=audit(root,manifest,crosswalk)
 dest=base/'results';dest.mkdir(parents=True,exist_ok=True);tag=uuid4().hex
 jp=dest/('coverage_'+tag+'.json');cp=dest/('coverage_'+tag+'.csv')
 jp.write_text(json.dumps({'summary':summary,'dates':rows},indent=2)+'\n',encoding='utf-8')
 fields=['date','phase','status','provider_rows','official_reference_rows','matched_games','missing_official_games','unmatched_provider_games','tipoff_conflicts','date_completeness','historical_asof','decision']
 with cp.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
 print(json.dumps({'report_json':str(jp),'report_csv':str(cp),**summary},indent=2))
if __name__=='__main__':main()
