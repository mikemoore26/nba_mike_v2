"""S8.12 read-only local pipeline mapping; no imports of project code, no fitting."""
from __future__ import annotations
import argparse, ast, csv, hashlib, json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOTS = ('src/nba_mike', 'research/p0_s4')
BUILDERS = {'build_opportunity_research_frame', 'make_form_frame'}
TARGETS = {'build_player_game_targets'}
FIT_CALLS = {'fit', 'fit_transform', 'partial_fit', 'fit_predict', 'train', 'fit_resample'}
PREDICT_CALLS = {'predict', 'predict_proba', 'transform', 'decision_function'}
SPLIT_CALLS = {'train_test_split', 'TimeSeriesSplit', 'KFold', 'StratifiedKFold', 'GroupKFold'}
WATCH = BUILDERS | TARGETS | FIT_CALLS | PREDICT_CALLS | SPLIT_CALLS | {'validate_predictors', 'validate_chronological_fold', 'assert_research_only', 'read_csv', 'to_csv', 'merge', 'join', 'concat', 'drop', 'dropna', 'sort_values', 'groupby', 'DataFrame'}
PRIORITY = ('research/p0_s4/s4/run_s4_1_acceptance.py', 'research/p0_s4/s4/run_s4_opportunity_research.py', 'research/p0_s4/s5/run_s5.py', 'research/p0_s4/s5_1/run_s5_1.py', 'research/p0_s4/s6/run_s6.py')

def call_name(node):
 if isinstance(node, ast.Name): return node.id
 if isinstance(node, ast.Attribute): return node.attr
 return ''

def names(node):
 return sorted({n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)})

def enclosing(node, parents):
 cur = node
 while cur in parents:
  cur = parents[cur]
  if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
   return cur.name
 return '<module>'

def snippet(lines, line):
 return lines[line-1].strip()[:240] if 0 < line <= len(lines) else ''

def analyze_file(root, rel):
 path=root/rel; source=path.read_text(encoding='utf-8-sig'); lines=source.splitlines(); tree=ast.parse(source)
 parents={child:parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
 calls=[];edges=[]
 for node in ast.walk(tree):
  fn=enclosing(node,parents)
  if isinstance(node, ast.Call):
   name=call_name(node.func)
   if name in WATCH:
    category=('FEATURE_BUILDER' if name in BUILDERS else 'TARGET_BUILDER' if name in TARGETS else 'FIT_OR_TRAIN' if name in FIT_CALLS else 'PREDICTION_OR_TRANSFORM' if name in PREDICT_CALLS else 'SPLIT' if name in SPLIT_CALLS else 'CONTRACT' if name.startswith(('validate_', 'assert_')) else 'DATA_OPERATION')
    calls.append(dict(path=rel,line=node.lineno,scope=fn,call=name,category=category,evidence=snippet(lines,node.lineno),classification='SOURCE_CALL_ONLY'))
  if isinstance(node,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
   val=node.value
   if val is None: continue
   targets=node.targets if isinstance(node,ast.Assign) else [node.target]
   lhs=sorted({n.id for target in targets for n in ast.walk(target) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)})
   rhs=names(val)
   source_calls=sorted({call_name(n.func) for n in ast.walk(val) if isinstance(n,ast.Call) and call_name(n.func) in WATCH})
   for dest in lhs:
    edges.append(dict(path=rel,line=node.lineno,scope=fn,assigned=dest,depends_on=';'.join(rhs),calls=';'.join(source_calls),evidence=snippet(lines,node.lineno),classification='LOCAL_SYNTAX_DEPENDENCY_NOT_RUNTIME_LINEAGE'))
 return calls,edges,hashlib.sha256(path.read_bytes()).hexdigest()

def scan(root):
 calls=[];edges=[];hashes={};issues=[];count=0
 for dirname in ROOTS:
  folder=root/dirname
  if not folder.is_dir():issues.append('MISSING_ROOT:'+dirname);continue
  for path in sorted(folder.rglob('*.py')):
   rel=path.relative_to(root).as_posix();count+=1
   try:
    c,e,d=analyze_file(root,rel);calls+=c;edges+=e
    if rel in PRIORITY:hashes[rel]=d
   except (SyntaxError,UnicodeError,OSError) as exc:issues.append('SCAN_ERROR:'+rel+':'+str(exc))
 for rel in PRIORITY:
  if rel not in hashes:issues.append('MISSING_PRIORITY:'+rel)
 return calls,edges,hashes,issues,count

def make_paths(calls,edges):
 out=[]
 for rel in PRIORITY:
  fc=[c for c in calls if c['path']==rel and c['category'] in ('FEATURE_BUILDER','TARGET_BUILDER','FIT_OR_TRAIN','PREDICTION_OR_TRANSFORM','SPLIT','CONTRACT')]
  ee=[e for e in edges if e['path']==rel]
  for c in fc:
   nearby=[e for e in ee if e['scope']==c['scope'] and (c['call'] in e['calls'] or abs(e['line']-c['line'])<=2)]
   out.append(dict(path=rel,line=c['line'],scope=c['scope'],call=c['call'],category=c['category'],local_assignments=';'.join(sorted({e['assigned'] for e in nearby})),evidence=c['evidence'],conclusion='CALL_SITE_ONLY_NO_INTERPROCEDURAL_PROOF'))
 return out

def summarize(calls,edges,issues,files,hashes):
 fits=[c for c in calls if c['category']=='FIT_OR_TRAIN']
 splits=[c for c in calls if c['category']=='SPLIT']
 contract=[c for c in calls if c['category']=='CONTRACT']
 return {'milestone':'S8.12','mode':'READ_ONLY_PIPELINE_BOUNDARY_MAPPING','run_utc':datetime.now(timezone.utc).isoformat(),
  'status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','training_eligible':False,
  'files_scanned':files,'call_sites':len(calls),'assignment_edges':len(edges),
  'fit_or_train_call_candidates':len(fits),'split_call_candidates':len(splits),'contract_call_candidates':len(contract),
  'priority_source_sha256':hashes,'issues':issues,
  'outcome':'BOUNDARY_MAPPING_ONLY_NOT_INTEGRATED',
  'recommended_boundary':'A future centrally controlled train/predict service must require an independently approved as-of feature manifest, validated predictor allowlist, independent pregame population, strict chronological folds, and fold-local transforms before fitting; S8.12 does not implement that service.',
  'gates':{'G1_research_call_site_mapping':'SOURCE_TRACED' if not issues else 'INCOMPLETE',
   'G2_live_training_matrix':'NOT_IDENTIFIED_OR_INSTRUMENTED',
   'G3_contract_enforced_at_all_training_paths':'NOT_INTEGRATED',
   'G4_fold_local_preprocessing_and_calibration':'NOT_VERIFIED',
   'G5_independent_pregame_population':'BLOCKED_INDEPENDENT_SOURCE',
   'G6_historical_asof_publication':'BLOCKED_SOURCE_PROVENANCE',
   'G7_restart_88_games':'UNVERIFIED'},
  'limitations':['AST call names are not resolved imports; .fit may be unrelated to model fitting.',
   'Local assignments are not runtime/interprocedural dataflow or proof of feature safety.',
   'Dynamic imports, notebooks, SQL and external jobs are outside this scan.',
   'No model, preprocessing, calibrator, network, or training function is executed.',
   'No synthetic allowlist is certified for production or historical pregame use.']}

def run(root):
 calls,edges,hashes,issues,files=scan(root)
 return summarize(calls,edges,issues,files,hashes),calls,edges,make_paths(calls,edges)

def write_csv(path,rows,fields):
 with path.open('w',newline='',encoding='utf-8') as fh:
  w=csv.DictWriter(fh,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');p.add_argument('--output-dir');a=p.parse_args(argv)
 root=Path(a.project_root).resolve();report,calls,edges,paths=run(root)
 out=Path(a.output_dir).resolve() if a.output_dir else root/'research/p0_s8/s8_12/results';out.mkdir(parents=True,exist_ok=True)
 write_csv(out/'s8_12_call_sites.csv',calls,['path','line','scope','call','category','evidence','classification'])
 write_csv(out/'s8_12_assignment_edges.csv',edges,['path','line','scope','assigned','depends_on','calls','evidence','classification'])
 write_csv(out/'s8_12_priority_paths.csv',paths,['path','line','scope','call','category','local_assignments','evidence','conclusion'])
 (out/'s8_12_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'files_scanned':report['files_scanned'],'call_sites':report['call_sites'],'fit_candidates':report['fit_or_train_call_candidates'],'issues':report['issues'],'decision':report['decision']},indent=2))
 return 1 if report['issues'] else 0
if __name__=='__main__':raise SystemExit(main())
