"""S8.6 read-only, heuristic static code audit. No training or modification."""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOTS = ('src/nba_mike', 'research/p0_s4')
PATTERNS = (
    ('NEGATIVE_SHIFT', 'HIGH', 'negative shift may look forward in time', ('.shift(-', 'shift(-')),
    ('CENTERED_ROLLING', 'HIGH', 'centered rolling windows can include future rows', ('center=True', 'center = True')),
    ('RANDOM_SPLIT', 'HIGH', 'random train/test split requires chronological review', ('train_test_split(', 'ShuffleSplit(', 'KFold(', 'cross_val_score(')),
    ('PREPROCESSING_FIT', 'MEDIUM', 'verify fit uses training fold only', ('.fit_transform(', '.fit(')),
    ('ROLLING_OR_EXPANDING', 'MEDIUM', 'verify grouping, sorting, shift, and exclusion of target game', ('.rolling(', '.expanding(', '.ewm(')),
    ('BACKFILL', 'HIGH', 'backfill can import future observations', ('.bfill(', 'method="bfill"', "method='bfill'")),
    ('POSTGAME_FIELD', 'MEDIUM', 'inspect whether game result field is a target or same-game predictor', ('["min"]', "['min']", '["pts"]', "['pts']", '["reb"]', "['reb']", '["ast"]', "['ast']", '["fg3m"]', "['fg3m']")),
    ('PARTICIPANT_UNIVERSE', 'MEDIUM', 'postgame player logs do not establish a pregame eligible-player universe', ('player_gamelogs', 'player_game_logs', 'gamelog')),
    ('CHRONOLOGICAL_SORT', 'INFO', 'inspect chronology implementation and season/player boundaries', ('.sort_values(', 'sort_index(', 'event_date')),
)

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inspect_file(path: Path, root: Path):
    text = path.read_text(encoding='utf-8-sig', errors='replace')
    lines = text.splitlines()
    relative = path.relative_to(root).as_posix()
    try:
        tree = ast.parse(text, filename=relative)
    except SyntaxError as exc:
        return {'path': relative, 'sha256': sha(path), 'parsed': False, 'functions': [], 'findings': [{
            'path': relative, 'line': exc.lineno or 0, 'function': '', 'rule': 'SYNTAX_ERROR', 'severity': 'HIGH',
            'evidence': str(exc.msg), 'explanation': 'AST scan incomplete; inspect file manually', 'classification': 'REVIEW_REQUIRED_NOT_CONFIRMED'}]}
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({'name': node.name, 'line': node.lineno, 'end_line': node.end_lineno})
    findings = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        enclosing = [f for f in functions if f['line'] <= i <= f['end_line']]
        function = min(enclosing, key=lambda f: f['end_line'] - f['line'])['name'] if enclosing else '<module>'
        for rule, severity, explanation, needles in PATTERNS:
            if any(needle in line for needle in needles):
                findings.append({'path': relative, 'line': i, 'function': function, 'rule': rule,
                                 'severity': severity, 'evidence': stripped[:220], 'explanation': explanation,
                                 'classification': 'REVIEW_REQUIRED_NOT_CONFIRMED'})
    return {'path': relative, 'sha256': sha(path), 'parsed': True, 'functions': functions, 'findings': findings}

def discover(root: Path):
    paths = set()
    for sub in ROOTS:
        base = root / sub
        if base.is_dir():
            paths.update(p for p in base.rglob('*.py') if not any(part in {'__pycache__', '.venv', 'results'} for part in p.parts))
    return sorted(paths)

def audit(root: Path):
    files = discover(root)
    scanned = [inspect_file(p, root) for p in files]
    findings = [f for item in scanned for f in item['findings']]
    relevant = [item for item in scanned if ('/s5' in item['path'] or '/s6' in item['path'] or '/features/' in item['path'] or '/evaluation/' in item['path'])]
    return {'milestone': 'S8.6', 'mode': 'READ_ONLY_HEURISTIC_SOURCE_AUDIT', 'status': 'RESEARCH_ONLY',
            'decision': 'BLOCK_TRAINING', 'training_eligible': False,
            'run_utc': datetime.now(timezone.utc).isoformat(), 'roots_requested': list(ROOTS),
            'roots_present': [sub for sub in ROOTS if (root/sub).is_dir()],
            'files_scanned': len(files), 's5_s6_feature_evaluation_files': len(relevant),
            'parse_failures': sum(not item['parsed'] for item in scanned),
            'finding_counts': dict(Counter(f['rule'] for f in findings)),
            'severity_counts': dict(Counter(f['severity'] for f in findings)),
            'confirmed_leakage_count': 0,
            'audit_completeness': 'PARTIAL_SOURCE_SCOPE' if len(relevant) == 0 else 'HEURISTIC_ONLY',
            'files': [{k: v for k, v in item.items() if k != 'findings'} for item in scanned],
            'findings': findings,
            'required_manual_gates': [
                'Trace each prediction feature from input source to as-of timestamp and target-game exclusion',
                'Verify rolling windows shift strictly before prediction game, grouped by player and chronological date',
                'Verify season boundaries, identity joins, and late corrections',
                'Verify fold-local preprocessing, hyperparameter search and calibration in walk-forward splits',
                'Establish pregame player universe and missing/DNP reconciliation independent of postgame participation',
                'Resolve or explicitly exclude 88 unverified 2019-20 restart games',
                'Review dynamic imports, notebooks, SQL, CSV joins, and non-Python pipelines not covered by scanner'],
            'limitations': ['Static string-pattern matches are review candidates, not confirmed defects',
                            'No data lineage or pre-tipoff source publication verified',
                            'No code executed beyond scanner; no models trained',
                            'Absence of findings is not evidence of leakage safety']}

def write_csv(path, rows, fields):
    with path.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction='ignore')
        writer.writeheader(); writer.writerows(rows)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', default='.')
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    if not (root / 'research').exists() and not (root / 'src').exists():
        parser.error('No project research/ or src/ directory found; refusing misleading empty scan')
    report = audit(root)
    out = root / 'research/p0_s8/s8_6/results'
    out.mkdir(parents=True, exist_ok=True)
    (out / 's8_6_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    write_csv(out/'s8_6_findings.csv', report['findings'], ['path','line','function','rule','severity','evidence','explanation','classification'])
    write_csv(out/'s8_6_file_inventory.csv', report['files'], ['path','sha256','parsed'])
    print(json.dumps({k: report[k] for k in ('milestone','decision','files_scanned','s5_s6_feature_evaluation_files','parse_failures','finding_counts','audit_completeness')}, indent=2))
    print('Outputs:', out)

if __name__ == '__main__':
    main()
