"""S8.7 targeted read-only source tracing; never grants training eligibility."""
import argparse
import ast
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TARGETS = {
 'src/nba_mike/features/opportunity.py': 'FEATURE_TARGET_BOUNDARY',
 'src/nba_mike/features/adaptive_form.py': 'PLAYER_DAY_CHRONOLOGY',
 'src/nba_mike/targets/builder.py': 'TARGET_ONLY_CONTRACT',
 'research/p0_s4/s4/run_s4_opportunity_research.py': 'POSTGAME_PARTICIPANT_UNIVERSE',
 'research/p0_s4/s5_1/run_s5_1.py': 'POSTGAME_PARTICIPANT_UNIVERSE',
 'research/p0_s4/s6/run_s6.py': 'POSTGAME_PARTICIPANT_UNIVERSE',
}
FIELDS = ('path','line','function','rule','severity','evidence','explanation','classification')

def load_csv(path):
    if not path.exists(): return []
    with path.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def digest(data): return hashlib.sha256(data).hexdigest()

def enclosing_function(tree, line):
    matches=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.lineno<=line<=getattr(n,'end_lineno',n.lineno)]
    return min(matches,key=lambda n:n.end_lineno-n.lineno) if matches else None

def trace_source(path, source, findings, expected_hash=None):
    lines=source.splitlines()
    tree=ast.parse(source,filename=path)
    funcs=[]
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            if any(int(f['line'])>=n.lineno and int(f['line'])<=n.end_lineno for f in findings):
                funcs.append({'name':n.name,'start_line':n.lineno,'end_line':n.end_lineno,'parameters':[a.arg for a in n.args.args], 'returns':ast.unparse(n.returns) if n.returns else None})
    cases=[]
    for f in findings:
        line=int(f['line']); fn=enclosing_function(tree,line)
        excerpt='\n'.join(f'{i+1}: {lines[i]}' for i in range(max(0,line-4),min(len(lines),line+3)))
        cases.append({'path':path,'line':line,'function':fn.name if fn else f['function'],'rule':f['rule'], 'severity':f['severity'], 'excerpt':excerpt,'status':'REVIEW_REQUIRED_NOT_CONFIRMED'})
    return {'path':path,'sha256':digest(source.encode('utf-8')),'expected_sha256':expected_hash,'hash_matches_inventory':None if expected_hash is None else digest(source.encode('utf-8'))==expected_hash,'functions':funcs,'findings':cases}

def audit(project, findings_path, inventory_path, output):
    findings=load_csv(findings_path)
    inventory={r['path']:r['sha256'] for r in load_csv(inventory_path)}
    selected=[f for f in findings if f.get('severity')=='MEDIUM' and f.get('path') in TARGETS]
    report={'milestone':'S8.7','mode':'READ_ONLY_TARGETED_SOURCE_TRACE','run_utc':datetime.now(timezone.utc).isoformat(), 'decision':'BLOCK_TRAINING','status':'RESEARCH_ONLY','training_eligible':False,'source_roots':list(TARGETS),'files':[], 'issues':[], 'findings_selected':len(selected),'limitations':['Line excerpts and AST signatures are not executable lineage proof','Mutation testing against actual S5/S6 functions is not performed by this read-only package','No pregame participant universe or timestamped source provenance established']}
    for rel,gate in TARGETS.items():
        path=project/rel
        relevant=[f for f in selected if f['path']==rel]
        if not path.is_file():
            report['files'].append({'path':rel,'status':'MISSING_SOURCE','gate':gate})
            report['issues'].append({'path':rel,'status':'SOURCE_REQUIRED','detail':'Source file not present in local checkout'})
            continue
        raw=path.read_bytes()
        try:
            parsed=trace_source(rel,raw.decode('utf-8-sig'),relevant,inventory.get(rel))
            parsed['actual_sha256_bytes']=digest(raw)
            parsed['hash_matches_inventory']=None if rel not in inventory else digest(raw)==inventory[rel]
            parsed['status']='SOURCE_TRACED_NOT_VERIFIED'
            parsed['gate']=gate
            if parsed['hash_matches_inventory'] is False:
                report['issues'].append({'path':rel,'status':'SOURCE_CHANGED','detail':'Current file hash differs from S8.6 inventory; findings may be stale'})
            report['files'].append(parsed)
        except (SyntaxError,UnicodeDecodeError,ValueError) as exc:
            report['files'].append({'path':rel,'status':'PARSE_FAILED','error':str(exc),'gate':gate})
            report['issues'].append({'path':rel,'status':'PARSE_FAILED','detail':str(exc)})
    report['counts']=dict(Counter(f['status'] for f in report['files']))
    report['gates']=[
      {'id':'G1','question':'Does each feature at game t stay invariant if outcome fields at game t and later are changed?','status':'NOT_TESTED'},
      {'id':'G2','question':'Are rolling features grouped by stable player ID and strictly earlier event dates, including same-day games?','status':'NOT_TESTED'},
      {'id':'G3','question':'Is target_minutes excluded from predictor feature lists and downstream transforms?','status':'NOT_TESTED'},
      {'id':'G4','question':'Does prediction population come from independent pregame roster/availability snapshots?','status':'BLOCKED_INDEPENDENT_SOURCE'},
      {'id':'G5','question':'Are training transformations and calibration fit only inside chronological training folds?','status':'NOT_TESTED'},
    ]
    output.mkdir(parents=True,exist_ok=True)
    (output/'s8_7_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    with (output/'s8_7_trace.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['path','line','function','rule','severity','status','excerpt']);writer.writeheader()
        for file in report['files']:
            for item in file.get('findings',[]):writer.writerow({k:item.get(k,'') for k in writer.fieldnames})
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',type=Path,default=Path('.'))
    p.add_argument('--findings',type=Path);p.add_argument('--inventory',type=Path)
    args=p.parse_args();project=args.project_root.resolve()
    previous=project/'research/p0_s8/s8_6/results'
    findings=args.findings or previous/'s8_6_findings.csv'
    inventory=args.inventory or previous/'s8_6_file_inventory.csv'
    if not findings.is_file() or not inventory.is_file():p.error('S8.6 findings/inventory not found; pass --findings and --inventory to the uploaded CSV paths')
    report=audit(project,findings,inventory,project/'research/p0_s8/s8_7/results')
    print(json.dumps({'files':report['counts'],'selected_medium_findings':report['findings_selected'],'issues':len(report['issues']),'decision':report['decision']},indent=2))
if __name__=='__main__':main()
