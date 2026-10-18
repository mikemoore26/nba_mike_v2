"""S8.22.10.28 static pipeline contract inventory. Does not import or execute repository modules."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

MILESTONE = 'S8.22.10.28'
SKIP = {'.git','.venv','venv','__pycache__','.pytest_cache','node_modules','results','outputs','output','data','dist','build'}
STAGES = {
 'identity': ('identity','roster','canonical'),
 'ingestion': ('ingest','capture','acquire','source','snapshot','reconstruction'),
 'minutes_features': ('minutes','opportunity','feature','adaptive_form','role_aware'),
 'predictions': ('predict','model','inference','forecast'),
 'evaluation': ('evaluat','validat','diagnostic','backtest','calibrat'),
 'market_tickets': ('market','odds','ticket','ledger','tracking','parlay'),
}

def safe_path(root: Path, path: Path) -> bool:
 return path.is_relative_to(root) and not any(x in SKIP or x.startswith('.') for x in path.relative_to(root).parts)

def classify(path: str) -> list[str]:
 p=path.lower(); return [k for k,words in STAGES.items() if any(w in p for w in words)]

def extract(root: Path, file: Path) -> dict:
 relative=file.relative_to(root).as_posix()
 source=file.read_bytes()
 record={'path':relative,'sha256':hashlib.sha256(source).hexdigest(),'stages':classify(relative), 'parse_status':'OK','imports':[],'functions':[],'classes':[],'main_guard':False,'test_candidates':[]}
 try: tree=ast.parse(source,filename=relative)
 except (SyntaxError,UnicodeDecodeError,ValueError):
  record['parse_status']='PARSE_FAILED';return record
 for node in tree.body:
  if isinstance(node,ast.Import):record['imports'] += [n.name for n in node.names]
  elif isinstance(node,ast.ImportFrom):record['imports'].append(node.module or '<relative>')
  elif isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
   args=node.args
   names=[a.arg for a in args.posonlyargs+args.args+args.kwonlyargs]
   if args.vararg:names.append('*'+args.vararg.arg)
   if args.kwarg:names.append('**'+args.kwarg.arg)
   record['functions'].append({'name':node.name,'parameters':names,'async':isinstance(node,ast.AsyncFunctionDef)})
  elif isinstance(node,ast.ClassDef):record['classes'].append(node.name)
  elif isinstance(node,ast.If):
   try:
    c=ast.unparse(node.test)
    if '__name__' in c and '__main__' in c:record['main_guard']=True
   except Exception:pass
 record['imports']=sorted(set(record['imports']))
 return record

def select(files: list[Path],root:Path,limit:int) -> list[Path]:
 def rank(p):
  s=p.relative_to(root).as_posix(); stages=classify(s)
  return (0 if s.startswith('src/nba_mike/') else 1 if s.startswith('scripts/') else 2 if s.startswith('research/') else 3, 0 if stages else 1,len(s),s)
 candidates=[p for p in files if not p.relative_to(root).as_posix().startswith('tests/') and classify(p.relative_to(root).as_posix())]
 # Guarantee stage coverage before filling ranked slots.
 selected=[]
 for stage in STAGES:
  matching=sorted((p for p in candidates if stage in classify(p.relative_to(root).as_posix())),key=rank)
  if matching and matching[0] not in selected:selected.append(matching[0])
 for p in sorted(candidates,key=rank):
  if len(selected)>=limit:break
  if p not in selected:selected.append(p)
 return selected[:limit]

def run(root:Path,out:Path,limit:int=36) -> dict:
 root=root.resolve();out=out.resolve()
 if not root.is_dir():raise ValueError('project root must exist')
 if not out.is_relative_to(root):raise ValueError('output must be inside project root')
 if limit<6 or limit>100:raise ValueError('limit must be between 6 and 100')
 files=sorted(p for p in root.rglob('*.py') if p.is_file() and safe_path(root,p))
 chosen=select(files,root,limit)
 records=[extract(root,p) for p in chosen]
 for rec in records:
  stem=Path(rec['path']).stem
  rec['test_candidates']=[p.relative_to(root).as_posix() for p in files if p.relative_to(root).as_posix().startswith('tests/') and (stem in p.stem or stem.replace('builder','') in p.stem and len(stem)>8)][:8]
 counts={s:sum(s in r['stages'] for r in records) for s in STAGES}
 data={'milestone':MILESTONE,'captured_at_utc':datetime.now(timezone.utc).isoformat(),'method':'STATIC_AST_ONLY_NO_IMPORT_NO_EXECUTION','total_python_files_in_scope':len(files),'selected_count':len(records),'stage_counts_selected':counts,'components':records,'limitations':['Signatures are syntactic only; no runtime compatibility proven','Filename-based stages and test links are heuristics','No model performance, data provenance, odds, or ticket validity certified','Source bodies, environment variables, credentials, and data rows are not exported'],'research_status':'RESEARCH_ONLY','training_decision':'BLOCK_TRAINING','real_money_approval':'DENIED','next_action':'Inspect selected interfaces and execute controlled offline fixture tests only after review'}
 out.mkdir(parents=True,exist_ok=True)
 (out/'contract_audit.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
 lines=[f'# {MILESTONE} — Pipeline contract inventory','','**STATIC ONLY — RESEARCH_ONLY / BLOCK_TRAINING / REAL-MONEY DENIED**','',f'Python files in scope: {len(files)}. Selected: {len(records)}.','', '| Stage | Selected components |','|---|---:|']
 lines += [f'| {s} | {n} |' for s,n in counts.items()]
 lines += ['','## Selected components','', '| File | Stages | Functions | Tests (heuristic) |','|---|---|---:|---:|']
 for r in records:lines.append(f"| `{r['path']}` | {', '.join(r['stages'])} | {len(r['functions'])} | {len(r['test_candidates'])} |")
 lines += ['','## Important limits','','- AST inspection never imports or runs project modules.','- Filename labels and nearby tests do not certify runtime behavior.','- No as-of data, model OOS, calibration, live odds, or ticket workflow is approved.','- Review `contract_audit.json` for function parameters and imports.','- Do not train models or place real-money bets based on this report.','']
 (out/'contract_audit.md').write_text('\n'.join(lines),encoding='utf-8')
 return data

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--project-root',type=Path,default=Path.cwd());p.add_argument('--out',type=Path);p.add_argument('--limit',type=int,default=36)
 a=p.parse_args();root=a.project_root.resolve();out=a.out or root/'research/p0_s8/s8_22_10_28/results'
 data=run(root,out,a.limit)
 print(f"[{MILESTONE}] selected={data['selected_count']} python_files={data['total_python_files_in_scope']} status=RESEARCH_ONLY")
 print(f'Outputs: {out / "contract_audit.json"} ; {out / "contract_audit.md"}')
if __name__=='__main__':main()
