"""S8.11 offline contract-integration feasibility. NO model fitting or network."""
from __future__ import annotations
import argparse,ast,csv,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd

ROOTS=('src/nba_mike','research/p0_s4')
WATCH=('fit','fit_transform','predict','predict_proba','train_test_split','TimeSeriesSplit','Pipeline','ColumnTransformer','StandardScaler','CalibratedClassifierCV','validate_predictors','build_opportunity_research_frame','make_form_frame','build_player_game_targets')
DENIED=frozenset(('min','pts','reb','ast','fg3m','target_minutes','target_points','target_rebounds','target_assists','target_3pm'))
CANDIDATES={'opportunity':['prior_games','prior_minutes','minutes_last3_avg','minutes_last5_avg','minutes_last10_avg','minutes_season_avg'],
'adaptive_form':['prior_games','prior_dates','last_3','last_5','season']}

def locate(root):
 rows=[];files=0;errors=[]
 for dirname in ROOTS:
  d=root/dirname
  if not d.is_dir():errors.append('MISSING_ROOT:'+dirname);continue
  for p in sorted(d.rglob('*.py')):
   files+=1
   try: tree=ast.parse(p.read_text(encoding='utf-8-sig'))
   except (SyntaxError,UnicodeError) as e:errors.append(f'PARSE:{p.relative_to(root)}:{e}');continue
   for node in ast.walk(tree):
    if not isinstance(node,ast.Call):continue
    f=node.func
    name=f.attr if isinstance(f,ast.Attribute) else f.id if isinstance(f,ast.Name) else ''
    if name not in WATCH:continue
    lines=p.read_text(encoding='utf-8-sig').splitlines()
    rows.append({'path':p.relative_to(root).as_posix(),'line':node.lineno,'call':name,
      'excerpt':lines[node.lineno-1].strip()[:260], 'classification':'REVIEW_ONLY_NOT_ENFORCEMENT'})
 return rows,files,errors

def exercise(root):
 sys.path.insert(0,str(root))
 sys.path.insert(0,str(root/'src'))
 from nba_mike.features.opportunity import build_opportunity_research_frame
 from nba_mike.features.adaptive_form import make_form_frame
 from research.p0_s8.s8_10.contract import validate_predictors,ContractViolation,assert_research_only
 rows=[]
 x=pd.DataFrame([{'game_id':f'{p}{i}','event_date':f'2025-01-{i+1:02d}','player_id':p,
 'team_id':f'T{p}','min':float(18+i),'pts':float(8+i),'reb':float(2+i%3),'ast':float(1+i%3),'fg3m':float(i%2)}
 for p in ('A','B') for i in range(8)])
 for name,builder in [('opportunity',build_opportunity_research_frame),('adaptive_form',make_form_frame)]:
  try:
   frame=builder(x.copy());columns=list(frame.columns)
   selected=CANDIDATES[name]
   if any(c not in columns for c in selected):raise ValueError('missing candidate columns: '+str([c for c in selected if c not in columns]))
   # Drop first-date cold starts rather than filling from outcomes. Do not train.
   eligible=frame.loc[frame[selected].notna().all(axis=1)].copy()
   if eligible.empty:raise ValueError('no non-null history rows')
   mat=validate_predictors(eligible,selected)
   rows.append({'check':name+'_explicit_candidate_matrix','status':'PASS','detail':f'{len(mat)} synthetic rows; columns={selected}; NOT as-of certified'})
   try:validate_predictors(eligible,selected+['target_minutes'])
   except ContractViolation:rows.append({'check':name+'_target_rejected','status':'PASS','detail':'target_minutes blocked'})
   else:rows.append({'check':name+'_target_rejected','status':'FAIL','detail':'target_minutes accepted'})
   # These retained outcomes must not enter candidate X even if present in source frame.
   present=[c for c in DENIED if c in columns]
   if any(c in mat.columns for c in DENIED):raise ValueError('outcome entered candidate X')
   rows.append({'check':name+'_no_outcomes_in_candidate_X','status':'PASS','detail':'retained source outcomes='+','.join(present)})
  except Exception as e:rows.append({'check':name+'_candidate_matrix','status':'FAIL','detail':f'{type(e).__name__}: {e}'})
 try:assert_research_only()
 except ContractViolation:rows.append({'check':'training_guard_remains_blocked','status':'PASS','detail':'BLOCK_TRAINING enforced by standalone guard'})
 else:rows.append({'check':'training_guard_remains_blocked','status':'FAIL','detail':'guard did not reject'})
 return rows

def run(root):
 calls,scanned,errors=locate(root)
 try:cases=exercise(root)
 except Exception as e:cases=[{'check':'imports_and_contract','status':'BLOCKED','detail':f'{type(e).__name__}: {e}'}]
 sources={}
 for path in ('research/p0_s8/s8_10/contract.py','src/nba_mike/features/opportunity.py','src/nba_mike/features/adaptive_form.py'):
  f=root/path;sources[path]=hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None
 counts={k:sum(r['status']==k for r in cases) for k in ('PASS','FAIL','BLOCKED')}
 return {'milestone':'S8.11','mode':'READ_ONLY_INTEGRATION_FEASIBILITY','run_utc':datetime.now(timezone.utc).isoformat(),
 'status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','training_eligible':False,
 'files_scanned':scanned,'entrypoint_candidates':len(calls),'counts':counts,'issues':errors,
 'source_sha256':sources,'outcome':'FEASIBILITY_ONLY_NOT_ENFORCED',
 'gates':{'G1_real_model_X_assembly':'NOT_IDENTIFIED_OR_INSTRUMENTED','G2_synthetic_candidate_contract':'PASS' if counts['FAIL']==counts['BLOCKED']==0 else 'NOT_PASSED',
 'G3_training_entrypoint_enforcement':'NOT_INTEGRATED','G4_fold_local_preprocessing':'NOT_VERIFIED',
 'G5_pregame_population':'BLOCKED_INDEPENDENT_SOURCE','G6_asof_timestamps':'BLOCKED_SOURCE_PROVENANCE'},
 'limitations':['Candidate allowlists are synthetic feasibility examples, NOT approved features',
 'No live fitted X, training pipeline, model or calibrator executed',
 'AST call locations are review candidates, not proof of use or safety',
 'Source columns may retain realized outcomes; downstream exclusion unverified',
 '88 restart games remain unverified']},calls,cases

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--project-root',default='.');ap.add_argument('--output-dir');a=ap.parse_args()
 root=Path(a.project_root).resolve();dest=Path(a.output_dir).resolve() if a.output_dir else root/'research/p0_s8/s8_11/results';dest.mkdir(parents=True,exist_ok=True)
 report,calls,cases=run(root)
 for filename,rows,fields in [('s8_11_entrypoints.csv',calls,['path','line','call','excerpt','classification']),('s8_11_cases.csv',cases,['check','status','detail'])]:
  with (dest/filename).open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 (dest/'s8_11_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'counts':report['counts'],'entrypoint_candidates':len(calls),'issues':report['issues'],'decision':report['decision']},indent=2))
 return 1 if report['counts']['FAIL'] or report['counts']['BLOCKED'] or report['issues'] else 0
if __name__=='__main__':raise SystemExit(main())
