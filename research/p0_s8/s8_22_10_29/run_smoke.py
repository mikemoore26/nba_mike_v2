"""S8.22.10.29: controlled existing-test smoke gate; no live APIs or model runs."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

SUITES = {
    'identity_canonical': ['tests/test_canonical_builder.py'],
    'schema_provenance': ['tests/test_schema_validation.py'],
    'd1_leakage': ['tests/test_leakage_invariants.py'],
    'opportunity_features': ['tests/test_opportunity_features.py'],
    'adaptive_form': ['tests/test_adaptive_form.py'],
}

def run(root: Path, *, timeout: int = 90, execute: bool = False) -> dict:
    root = root.resolve()
    if not (root / 'pyproject.toml').is_file() or not (root / 'src/nba_mike').is_dir():
        raise ValueError('Expected NBA_MIKE v2 root with pyproject.toml and src/nba_mike')
    results = []
    for name, paths in SUITES.items():
        missing = [p for p in paths if not (root / p).is_file()]
        item = {'suite': name, 'files': paths, 'status': 'MISSING_TEST' if missing else 'READY_NOT_EXECUTED', 'missing': missing}
        if execute and not missing:
            # Isolated subprocess, known repository test filenames only; no external fetch scripts.
            env = os.environ.copy()
            env['PYTHONPATH'] = str(root / 'src') + os.pathsep + env.get('PYTHONPATH', '')
            env['PYTHONDONTWRITEBYTECODE'] = '1'
            try:
                proc = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *paths],
                    cwd=root, env=env, capture_output=True, text=True, timeout=timeout, check=False)
                item.update(status='PASS' if proc.returncode == 0 else 'FAIL', exit_code=proc.returncode,
                    output=(proc.stdout + '\n' + proc.stderr)[-6000:])
            except subprocess.TimeoutExpired:
                item.update(status='TIMEOUT', output=f'Timeout after {timeout}s')
        results.append(item)
    return {
        'milestone': 'S8.22.10.29', 'captured_at_utc': datetime.now(timezone.utc).isoformat(),
        'method': 'EXISTING_PYTEST_SUITES' if execute else 'TEST_INVENTORY_ONLY',
        'suites': results,
        'all_smoke_passed': execute and all(r['status'] == 'PASS' for r in results),
        'research_status': 'RESEARCH_ONLY', 'training_decision': 'BLOCK_TRAINING',
        'real_money_approval': 'DENIED',
        'limits': ['Existing unit tests are not a pipeline integration test',
                   'No real as-of data, OOS performance, odds, or betting pipeline certified',
                   'Selected test modules are executed only with --execute; review them before running'],
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--project-root', type=Path, default=Path('.'))
    ap.add_argument('--execute', action='store_true', help='Execute five preselected local pytest modules')
    ap.add_argument('--timeout', type=int, default=90)
    args = ap.parse_args()
    if not 1 <= args.timeout <= 600:
        ap.error('--timeout must be 1..600')
    report = run(args.project_root, timeout=args.timeout, execute=args.execute)
    out = args.project_root.resolve() / 'research/p0_s8/s8_22_10_29/results'
    out.mkdir(parents=True, exist_ok=True)
    path = out / 'smoke_report.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('S8.22.10.29:', [(r['suite'], r['status']) for r in report['suites']])
    print('Report:', path)
    if args.execute and not report['all_smoke_passed']:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
