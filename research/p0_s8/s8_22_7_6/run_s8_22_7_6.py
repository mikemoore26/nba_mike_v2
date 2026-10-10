"""S8.22.7.6 offline evidence acquisition queue. Does not fetch or certify."""
import argparse,csv,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4

TARGETS={
 '2023-10-24':('regular','CONTROL_PRESERVE'),
 '2023-11-15':('regular','POSITIVE_DATE_SCHEDULE'),
 '2024-01-15':('regular','POSITIVE_DATE_SCHEDULE'),
 '2024-06-20':('offseason','NEGATIVE_DATE_SCHEDULE'),
 '2026-10-10':('preseason','PRESEASON_COVERAGE'),
}
TASK_FIELDS=['date','phase','task_type','priority','provider_rows','coverage_status','required_evidence','capture_receipt_path','source_integrity','review_status','notes']

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def safe_path(root,value):
 if not value:return None
 p=Path(value)
 if p.is_absolute() or '..' in p.parts:raise ValueError('UNSAFE_PATH')
 q=(root/p).resolve()
 if not q.is_relative_to(root):raise ValueError('UNSAFE_PATH')
 return q

def validate_receipt(root,receipt_path,date):
 if receipt_path is None:return 'NOT_SUPPLIED'
 if not receipt_path.is_file():return 'RECEIPT_NOT_FOUND'
 try:
  receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
  source=safe_path(root,receipt.get('evidence_path'))
  if receipt.get('date')!=date:return 'DATE_MISMATCH'
  url=receipt.get('source_url','')
  from urllib.parse import urlsplit
  parsed=urlsplit(url)
  if parsed.scheme!='https' or parsed.hostname not in {'nba.com','www.nba.com'} or parsed.username or parsed.password:return 'NOT_OFFICIAL_NBA_URL'
  if not source or not source.is_file():return 'SOURCE_BYTES_MISSING'
  if not isinstance(receipt.get('bytes'),int) or source.stat().st_size!=receipt['bytes'] or sha(source)!=receipt.get('sha256'):return 'SOURCE_INTEGRITY_MISMATCH'
  dt=datetime.fromisoformat(receipt.get('retrieved_utc','').replace('Z','+00:00'))
  if dt.tzinfo is None:return 'RETRIEVAL_TIME_INVALID'
  return 'PASS_BYTES_ONLY'
 except (ValueError,OSError,TypeError,KeyError,json.JSONDecodeError):return 'INVALID_RECEIPT'

def build_queue(root,coverage_report,receipts):
 data=json.loads(coverage_report.read_text(encoding='utf-8'))
 if data.get('summary',{}).get('milestone')!='S8.22.7.5':raise ValueError('WRONG_MILESTONE')
 dates=data.get('dates',[])
 if len(dates)!=len(TARGETS) or {r.get('date') for r in dates}!=set(TARGETS):raise ValueError('DATE_SET_MISMATCH')
 if data.get('summary',{}).get('decision')!='BLOCK_TRAINING':raise ValueError('UNEXPECTED_GOVERNANCE')
 tasks=[]
 for row in dates:
  date=row['date'];phase,kind=TARGETS[date]
  if row.get('phase')!=phase:raise ValueError('PHASE_MISMATCH')
  status=row.get('status','');n=row.get('provider_rows')
  if kind=='CONTROL_PRESERVE':
   priority='CONTROL';needed='Preserve existing official game pages and announcement review; no re-fetch';review='CANDIDATE_ONLY_NO_NEW_ACQUISITION'
  elif kind=='POSITIVE_DATE_SCHEDULE':
   priority='P1' if date=='2023-11-15' else 'P2';needed='Official NBA date-wide schedule listing all games, with archived receipt/source; per-game official pages as separate independent IDs';review='AWAITING_INDEPENDENT_DATE_EVIDENCE'
  elif kind=='NEGATIVE_DATE_SCHEDULE':
   priority='P3';needed='Official NBA date/season schedule evidence with explicit date coverage, plus manually reviewed negative-evidence statement; zero provider rows alone insufficient';review='AWAITING_NEGATIVE_DATE_EVIDENCE'
  else:
   priority='P4';needed='Official NBA preseason schedule for the specific date, with explicit preseason scope; investigate provider preseason coverage before interpreting zero rows';review='AWAITING_PRESEASON_COVERAGE'
  receipt=receipts.get(date,'')
  integrity=validate_receipt(root,safe_path(root,receipt),date) if receipt else 'NOT_SUPPLIED'
  if integrity!='NOT_SUPPLIED':review='CAPTURE_BYTES_VERIFIED_SEMANTIC_REVIEW_REQUIRED' if integrity=='PASS_BYTES_ONLY' else 'CAPTURE_INTEGRITY_FAILURE'
  tasks.append(dict(date=date,phase=phase,task_type=kind,priority=priority,provider_rows=n,coverage_status=status,required_evidence=needed,capture_receipt_path=receipt,source_integrity=integrity,review_status=review,notes='Manual source/date/phase/completeness review required; no automatic approval'))
 return tasks

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--project-root',default='.')
 parser.add_argument('--coverage-report',required=True,help='S8.22.7.5 JSON report, path relative to project root')
 parser.add_argument('--receipt-manifest',default='',help='Optional CSV: date,receipt_path; paths relative to project root')
 args=parser.parse_args(argv)
 root=Path(args.project_root).resolve();report=safe_path(root,args.coverage_report)
 if not report or not report.is_file():parser.error('coverage report not found')
 receipts={}
 if args.receipt_manifest:
  path=safe_path(root,args.receipt_manifest)
  if not path or not path.is_file():parser.error('receipt manifest not found')
  with path.open(newline='',encoding='utf-8-sig') as f:
   reader=csv.DictReader(f)
   if not reader.fieldnames or not {'date','receipt_path'}.issubset(reader.fieldnames):parser.error('invalid receipt manifest headers')
   for r in reader:
    d=r['date'].strip()
    if d not in TARGETS or d in receipts:parser.error('invalid/duplicate receipt date')
    receipts[d]=r['receipt_path'].strip()
 tasks=build_queue(root,report,receipts)
 out=root/'research/p0_s8/s8_22_7_6/results';out.mkdir(parents=True,exist_ok=True)
 token=uuid4().hex
 csv_path=out/f'acquisition_queue_{token}.csv';json_path=out/f'acquisition_queue_{token}.json'
 with csv_path.open('w',newline='',encoding='utf-8') as f:
  writer=csv.DictWriter(f,fieldnames=TASK_FIELDS);writer.writeheader();writer.writerows(tasks)
 result={'milestone':'S8.22.7.6','mode':'OFFLINE_EVIDENCE_QUEUE','input_coverage_sha256':sha(report),'generated_utc':datetime.now(timezone.utc).isoformat(),'tasks':tasks,'date_completeness':'NOT_CERTIFIED','historical_asof':'NOT_CERTIFIED','routine_collection_approved':False,'training_eligible':False,'decision':'BLOCK_TRAINING','limitations':['Receipt integrity does not prove schedule exhaustiveness or no-game claims','No NBA site accessed by this tool','2026 retrieval is not proof of 2023 pregame availability']}
 json_path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print('S8.22.7.6 OFFLINE QUEUE COMPLETE')
 print('CSV:',csv_path)
 print('JSON:',json_path)
 for t in tasks:print(t['date'],t['priority'],t['review_status'],t['source_integrity'])
 print('DECISION: BLOCK_TRAINING')
 return 0

if __name__=='__main__':raise SystemExit(main())
