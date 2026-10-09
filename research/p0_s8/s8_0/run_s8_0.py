"""S8.0 read-only NBA data/model readiness inventory; never trains or certifies data."""
from __future__ import annotations
import argparse, csv, hashlib, json, os, re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DATA_EXT={'.csv','.parquet','.jsonl','.feather'}
SKIP={'.git','.venv','venv','__pycache__','.pytest_cache','node_modules','results','objects','captures','input_pdfs'}
CATEGORIES={
 'minutes': ('minutes','min_projection','minute_model','minute'),
 'player_stats': ('player_stat','box_score','boxscore','game_log','player_game','pts','rebounds','assists'),
 'baseline_models': ('baseline','model','predict','training'),
 'validation': ('walk_forward','backtest','holdout','chronological','leakage','validation'),
 'market': ('odds','line','market','price'),
 'availability_roster': ('roster','injury','transaction','lineup','availability'),
}
SENSITIVE=('roster','injury','transaction','lineup','availability')
TIME_FIELDS=('as_of','asof','snapshot','published_at','publication_time','available_at','known_at','collected_at')
DATE_FIELDS=('game_date','event_date','date','season','game_id')
ID_FIELDS=('player_id','person_id','athlete_id','player_name')
TARGET_FIELDS=('minutes','min','pts','points','reb','rebounds','ast','assists','fg3m','threes')


def category(path):
 s=str(path).lower().replace('\\','/')
 return [k for k, terms in CATEGORIES.items() if any(t in s for t in terms)] or ['uncategorized']


def scan(root:Path, max_files=4000):
 """Inventory paths; only sample CSV headers, never load entire datasets."""
 rows=[]; skipped=0
 for dirpath, dirs, files in os.walk(root):
  dirs[:]=sorted(d for d in dirs if d not in SKIP and not d.startswith('.'))
  for filename in sorted(files):
   p=Path(dirpath)/filename; rel=p.relative_to(root).as_posix(); suffix=p.suffix.lower()
   if suffix not in DATA_EXT|{'.py','.ipynb','.md'}:continue
   if len(rows)>=max_files:skipped+=1;continue
   try: size=p.stat().st_size
   except OSError:continue
   cols=[]; header_error=''
   if suffix=='.csv':
    try:
     with p.open('r',encoding='utf-8-sig',newline='') as f: cols=next(csv.reader(f),[])
    except (OSError,UnicodeError,csv.Error) as e: header_error=type(e).__name__
   elif suffix=='.parquet':
    try:
     import pyarrow.parquet as pq
     cols=pq.read_schema(p).names
    except (ImportError,Exception) as e: header_error='PARQUET_SCHEMA_UNAVAILABLE:'+type(e).__name__
   rows.append({'path':rel,'suffix':suffix,'bytes':size,'categories':category(rel),
     'columns':cols,'header_error':header_error,'has_asof_column':any(any(t in c.lower() for t in TIME_FIELDS) for c in cols),
     'has_date_column':any(c.lower() in DATE_FIELDS for c in cols),
     'has_player_identifier':any(c.lower() in ID_FIELDS for c in cols),
     'has_target_column':any(c.lower() in TARGET_FIELDS for c in cols)})
 return rows,skipped


def evaluate(rows):
 findings=[]
 for component in CATEGORIES:
  matching=[r for r in rows if component in r['categories']]
  data=[r for r in matching if r['suffix'] in DATA_EXT]
  code=[r for r in matching if r['suffix']=='.py']
  known_schema=[r for r in data if r['columns']]
  blockers=[]
  if not matching: blockers.append('NO_MATCHING_PROJECT_FILES_DISCOVERED')
  if component in ('minutes','player_stats','market','availability_roster') and not data:
   blockers.append('NO_DATA_FILE_DISCOVERED')
  if component in ('baseline_models','validation') and not code:
   blockers.append('NO_IMPLEMENTATION_DISCOVERED')
  if data and not known_schema: blockers.append('NO_READABLE_SCHEMA')
  if component=='availability_roster':blockers.append('HISTORICAL_ASOF_PROVENANCE_NOT_VERIFIED_S7_51')
  if component in ('minutes','player_stats','market'):
   blockers.append('HISTORICAL_ASOF_PROVENANCE_NOT_AUDITED')
  if component in ('baseline_models','validation'):
   blockers.append('CHRONOLOGICAL_OOS_EXECUTION_NOT_VERIFIED')
  # Never certify training readiness based on filenames/headers alone.
  status='BLOCKED' if (not matching or component=='availability_roster') else 'NEEDS_REPAIR'
  findings.append({'component':component,'status':status,'matched_files':len(matching),
    'data_files':len(data),'python_files':len(code),'readable_data_schemas':len(known_schema),
    'blockers':blockers,'example_paths':[r['path'] for r in matching[:8]]})
 return findings


def run(project_root:Path, output_dir:Path, max_files=4000):
 project_root=project_root.resolve();output_dir=output_dir.resolve()
 if not project_root.is_dir():raise ValueError('Project root must exist')
 if project_root==output_dir:raise ValueError('Output directory must differ from project root')
 rows,skipped=scan(project_root,max_files)
 findings=evaluate(rows)
 output_dir.mkdir(parents=True,exist_ok=True)
 report={'milestone':'S8.0','mode':'READ_ONLY_INVENTORY','status':'RESEARCH_ONLY',
   'decision':'BLOCK_TRAINING','project_root':str(project_root),
   'scanned_files':len(rows),'files_excluded_by_scan_limit':skipped,
   'component_status_counts':dict(Counter(f['status'] for f in findings)),
   'components':findings,
   'historical_roster_transaction_features':'BLOCKED_S7_51',
   'historical_asof_training_eligible':False,
   'limitations':['No row-level data checks or baseline predictions executed',
     'Column names are only hints, never historical publication proof',
     'Parquet schema requires optional pyarrow',
     'A path match does not prove the file is a usable NBA dataset',
     'No model is approved for training or betting']}
 (output_dir/'s8_0_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 with (output_dir/'s8_0_inventory.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f);w.writerow(['path','suffix','bytes','categories','columns','header_error','has_asof_column','has_date_column','has_player_identifier','has_target_column'])
  for r in rows:w.writerow([r['path'],r['suffix'],r['bytes'],';'.join(r['categories']),';'.join(r['columns']),r['header_error'],r['has_asof_column'],r['has_date_column'],r['has_player_identifier'],r['has_target_column']])
 with (output_dir/'s8_0_component_review.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f);w.writerow(['component','status','matched_files','data_files','python_files','blockers','example_paths'])
  for r in findings:w.writerow([r['component'],r['status'],r['matched_files'],r['data_files'],r['python_files'],';'.join(r['blockers']),';'.join(r['example_paths'])])
 return report


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--project-root',type=Path,default=Path(__file__).resolve().parents[3])
 parser.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent/'results')
 parser.add_argument('--max-files',type=int,default=4000)
 args=parser.parse_args()
 if args.max_files<1:parser.error('--max-files must be positive')
 print(json.dumps(run(args.project_root,args.output_dir,args.max_files),indent=2))
if __name__=='__main__':main()
