"""S8.22.10.27: non-executing, read-only functional pipeline inventory.

No project modules are imported or executed. No network calls. No model loading.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SKIP = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache', 'node_modules', 'results', 'outputs', 'artifacts', 'data', 'raw', 'processed', '.mypy_cache'}
ROLE_TERMS = {
    'data_ingestion': ('ingest', 'fetch', 'download', 'collect', 'extract', 'capture'),
    'identity_rosters': ('roster', 'player_id', 'identity', 'team_member'),
    'injuries_lineups': ('injur', 'lineup', 'availability'),
    'minutes_opportunity': ('minute', 'usage', 'opportunity', 'rotation'),
    'features': ('feature',),
    'models_predictions': ('predict', 'inference', 'model', 'train'),
    'evaluation': ('backtest', 'calibrat', 'evaluate', 'validation', 'walk_forward'),
    'odds_market': ('odds', 'market', 'sportsbook', 'vig'),
    'tickets_tracking': ('ticket', 'parlay', 'ledger', 'paper_bet', 'grade'),
}
ARTIFACT_SUFFIXES = {'.pkl', '.pickle', '.joblib', '.onnx', '.pt', '.pth', '.cbm', '.xgb', '.lgb'}

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def classify(path: str, source: str) -> list[str]:
    value = (path + '\n' + source[:20000]).lower()
    return [role for role, terms in ROLE_TERMS.items() if any(term in value for term in terms)]

def analyze_python(path: Path, root: Path) -> dict:
    rel = path.relative_to(root).as_posix()
    result = {'path': rel, 'sha256': sha(path), 'roles': [], 'imports': [], 'cli_entry': False,
              'main_guard': False, 'functions': [], 'parse_error': None, 'runtime_checked': False}
    try:
        source = path.read_text(encoding='utf-8-sig')
        tree = ast.parse(source, filename=rel)
    except (UnicodeError, SyntaxError, OSError) as e:
        result['parse_error'] = f'{type(e).__name__}: {e}'
        return result
    result['roles'] = classify(rel, source)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add('.' * node.level + node.module)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and isinstance(getattr(node, 'name', None), str):
            if node.col_offset == 0:
                result['functions'].append(node.name)
        elif isinstance(node, ast.If):
            try:
                expression = ast.unparse(node.test)
                if '__name__' in expression and '__main__' in expression:
                    result['main_guard'] = True
            except Exception:
                pass
    result['imports'] = sorted(imports)
    result['cli_entry'] = result['main_guard'] or bool(re.search(r'\b(?:argparse|click|typer)\b', source))
    return result

def scan(root: Path, max_files: int = 30000) -> dict:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Project root must be a directory')
    python_files, artifacts, configs = [], [], []
    scanned = 0
    for path in root.rglob('*'):
        if any(part in SKIP or part.startswith('.git') for part in path.relative_to(root).parts):
            continue
        if path.is_symlink() or not path.is_file():
            continue
        scanned += 1
        if scanned > max_files:
            raise RuntimeError(f'File scan limit exceeded ({max_files}); no partial report written')
        rel = path.relative_to(root).as_posix()
        if path.suffix.lower() == '.py':
            python_files.append(analyze_python(path, root))
        elif path.suffix.lower() in ARTIFACT_SUFFIXES:
            artifacts.append({'path': rel, 'bytes': path.stat().st_size, 'sha256': sha(path),
                              'validated_for_inference': False})
        elif path.name.lower() in {'pyproject.toml', 'requirements.txt', 'requirements-dev.txt', 'setup.cfg', 'pytest.ini', 'environment.yml'}:
            configs.append({'path': rel, 'sha256': sha(path)})
    python_files.sort(key=lambda x: x['path'])
    artifacts.sort(key=lambda x: x['path'])
    role_counts = dict(sorted(Counter(role for p in python_files for role in p['roles']).items()))
    entrypoints = [{'path': p['path'], 'roles': p['roles'], 'main_guard': p['main_guard']}
                   for p in python_files if p['cli_entry']]
    errors = [{'path': p['path'], 'error': p['parse_error']} for p in python_files if p['parse_error']]
    return {
        'milestone': 'S8.22.10.27', 'project_root': str(root),
        'captured_at_utc': datetime.now(timezone.utc).isoformat(),
        'method': 'STATIC_AST_AND_FILENAME_SCAN_NO_EXECUTION',
        'scope_note': 'Excluded data/results/output folders; artifact inventory is partial by design.',
        'python_file_count': len(python_files), 'potential_cli_count': len(entrypoints),
        'model_artifact_count_in_scanned_paths': len(artifacts),
        'role_counts': role_counts, 'potential_entrypoints': entrypoints,
        'python_files': python_files, 'model_artifacts': artifacts,
        'config_files': configs, 'parse_errors': errors,
        'readiness': {
            'historical_data_gate': 'NOT_VERIFIED', 'current_season_data_gate': 'NOT_VERIFIED',
            'model_oos_gate': 'NOT_VERIFIED', 'market_odds_gate': 'NOT_VERIFIED',
            'paper_ticket_pipeline_gate': 'NOT_VERIFIED', 'real_money_approval': 'DENIED'
        },
        'research_status': 'RESEARCH_ONLY', 'training_decision': 'BLOCK_TRAINING',
        'interpretation': 'Candidates only. Imports, runtime behavior, provenance, and accuracy are not certified.',
        'next_checks': [
            'Manually select real entry points and inspect their contracts',
            'Identify required input datasets and historical as-of provenance',
            'Run isolated offline smoke tests with controlled fixtures',
            'Verify chronological out-of-sample evaluation and model artifact lineage',
            'Validate odds timestamping and paper-ledger accounting independently'
        ]
    }

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, default=None)
    parser.add_argument('--max-files', type=int, default=30000)
    args = parser.parse_args(argv)
    root = args.project_root.resolve(strict=True)
    result = scan(root, args.max_files)
    output = args.output or root / 'research/p0_s8/s8_22_10_27/results/functional_pipeline_audit.json'
    output = output.resolve()
    if not output.is_relative_to(root):
        parser.error('--output must be inside --project-root')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f'REPORT: {output}')
    print(f"Python: {result['python_file_count']} | CLI candidates: {result['potential_cli_count']} | parse errors: {len(result['parse_errors'])}")
    print('RESEARCH_ONLY / BLOCK_TRAINING / real-money DENIED')

if __name__ == '__main__':
    main()
