"""S8.9: read-only downstream predictor-lineage reconnaissance; never trains models."""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BANNED = frozenset({'min','pts','reb','ast','fg3m','target_minutes','target_pts','target_reb','target_ast','target_fg3m','target_points','target_rebounds','target_assists','target_threes'})
# Narrow, intentionally conservative. No heuristic auto-certification.
PATTERNS = {
    'FEATURE_BUILDER_CALL': re.compile(r'\b(?:build_opportunity_research_frame|make_form_frame)\s*\('),
    'MODEL_FIT': re.compile(r'\.fit\s*\('),
    'PREDICTOR_SELECTION': re.compile(r'\b(?:feature_cols|feature_columns|predictor_cols|predictors|X_train|X_test|X_valid|X_val|X\s*=|drop\s*\(|select_dtypes\s*\()'),
    'PREPROCESSING_OR_CALIBRATION': re.compile(r'\b(?:StandardScaler|MinMaxScaler|RobustScaler|SimpleImputer|KNNImputer|OneHotEncoder|PCA|CalibratedClassifierCV|IsotonicRegression|Pipeline|ColumnTransformer)\b'),
    'SPLIT_OR_CV': re.compile(r'\b(?:train_test_split|KFold|StratifiedKFold|TimeSeriesSplit|GroupKFold|cross_val_score|cross_validate|GridSearchCV|RandomizedSearchCV)\b'),
    'OUTCOME_COLUMN_REFERENCE': re.compile(r'[\[\(,]\s*[\'\"](?:min|pts|reb|ast|fg3m|target_minutes|target_pts|target_reb|target_ast|target_fg3m)[\'\"]'),
}
FIELDS = ['path','sha256','line','function','rule','evidence','classification']


def validate_predictor_columns(columns):
    """Explicit contract for *candidate* pregame feature column lists."""
    names = list(columns)
    if len(names) != len(set(names)):
        raise ValueError('duplicate predictor columns')
    forbidden = sorted(set(names) & BANNED)
    if forbidden:
        raise ValueError('realized/target columns prohibited: ' + ', '.join(forbidden))
    if not names:
        raise ValueError('empty predictor selection')
    return names


def function_at(tree, lineno):
    candidates = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.lineno <= lineno <= getattr(node, 'end_lineno', node.lineno):
            candidates.append((node.end_lineno - node.lineno, node.name))
    return min(candidates)[1] if candidates else '<module>'


def scan_source(relative_path, source):
    try:
        tree = ast.parse(source, filename=relative_path)
    except SyntaxError as exc:
        return [], {'path':relative_path,'error':f'SyntaxError at {exc.lineno}: {exc.msg}'}
    findings = []
    lines = source.splitlines()
    for number, line in enumerate(lines, 1):
        # Ignore comments; keep exact evidence for human review.
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        for rule, pattern in PATTERNS.items():
            if pattern.search(line):
                findings.append({'path':relative_path,'sha256':hashlib.sha256(source.encode('utf-8')).hexdigest(),
                                 'line':number,'function':function_at(tree, number),'rule':rule,
                                 'evidence':line.strip()[:350], 'classification':'MANUAL_REVIEW_REQUIRED'})
    return findings, None


def run(project_root, out_dir):
    project_root = Path(project_root).resolve()
    out_dir = Path(out_dir).resolve()
    files = []
    for sub in ('src/nba_mike', 'research/p0_s4'):
        root = project_root / sub
        if root.is_dir():
            files.extend(p for p in root.rglob('*.py') if p.is_file())
    files = sorted(set(files))
    findings, issues = [], []
    for path in files:
        rel = path.relative_to(project_root).as_posix()
        try:
            source = path.read_text(encoding='utf-8-sig')
        except (UnicodeError, OSError) as exc:
            issues.append({'path':rel,'error':str(exc)})
            continue
        hits, error = scan_source(rel, source)
        findings.extend(hits)
        if error:
            issues.append(error)
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir/'s8_9_findings.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader(); writer.writerows(findings)
    # This is NOT a verified list of model inputs; it is a source inspection queue.
    report = {
        'milestone':'S8.9', 'mode':'READ_ONLY_DOWNSTREAM_SOURCE_AUDIT',
        'run_utc':datetime.now(timezone.utc).isoformat(),
        'status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','training_eligible':False,
        'files_scanned':len(files),'findings_count':len(findings),
        'rule_counts':dict(sorted(Counter(f['rule'] for f in findings).items())),
        'issues':issues, 'outcome':'SOURCE_REVIEW_QUEUE_ONLY_NOT_PIPELINE_CERTIFICATION',
        'gates':{
            'G1_predictor_matrix_exact_columns':'NOT_VERIFIED',
            'G2_realized_target_columns_excluded_from_every_model':'NOT_VERIFIED',
            'G3_chronological_fold_boundaries':'NOT_VERIFIED',
            'G4_fold_local_preprocessing_and_calibration':'NOT_VERIFIED',
            'G5_independent_pregame_population':'BLOCKED_INDEPENDENT_SOURCE',
            'G6_historical_asof_provenance':'BLOCKED_SOURCE_PROVENANCE'},
        'limitations':[
            'Text/AST discovery only; cannot establish variable-level dataflow or dynamic imports',
            'Comments excluded, strings may still produce false positives',
            'Does not execute training or inspect live fitted matrices',
            'A missing finding does not certify absence of leakage',
            'No as-of source timestamps or pregame player eligibility evidence',
            'Synthetic predictor contract tests do not prove downstream callers use the contract'
        ]}
    (out_dir/'s8_9_report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', default='.')
    parser.add_argument('--out-dir', default=None)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    out = Path(args.out_dir) if args.out_dir else root/'research/p0_s8/s8_9/results'
    report = run(root, out)
    print(json.dumps({k:report[k] for k in ('milestone','files_scanned','findings_count','outcome','decision','issues')}, indent=2))

if __name__ == '__main__':
    main()
