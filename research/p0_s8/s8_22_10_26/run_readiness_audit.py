"""S8.22.10.26: conservative, read-only NBA_MIKE v2 opening-week inventory.

Static code discovery is NOT model validation or betting authorization.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

MILESTONE = 'S8.22.10.26'
CATEGORIES = {
 'schedule_and_games': (r'schedule', r'scoreboard', r'games?'),
 'roster_and_identity': (r'roster', r'player[_-]?id', r'identity'),
 'injuries_and_lineups': (r'injur', r'lineup', r'availab'),
 'minutes_and_opportunity': (r'minutes?', r'usage', r'opportunit', r'rotation'),
 'stat_predictions': (r'predict', r'projection', r'points?', r'rebounds?', r'assists?', r'threes?', r'model'),
 'validation_and_calibration': (r'validat', r'backtest', r'calibrat', r'walk[_-]?forward', r'holdout'),
 'market_and_odds': (r'odds', r'market', r'fan[_-]?duel', r'draft[_-]?kings', r'expected[_-]?value'),
 'ticket_and_parlay': (r'ticket', r'parlay', r'bet[_-]?slip', r'correlat'),
 'tracking_and_grading': (r'track', r'ledger', r'grad', r'paper[_-]?bet'),
}
SKIP = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'node_modules', 'results', 'output', 'outputs', 'data', 'artifacts', 'build', 'dist', '.tox'}
ALLOWED = {'.py', '.md', '.toml', '.yaml', '.yml', '.json', '.ini', '.cfg', '.txt'}
MAX_FILES = 15000
MAX_SIZE = 300_000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_files(root: Path):
    count = 0
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in ALLOWED:
            continue
        rel = path.relative_to(root)
        if any(part.lower() in SKIP for part in rel.parts[:-1]):
            continue
        if path.stat().st_size > MAX_SIZE:
            continue
        count += 1
        if count > MAX_FILES:
            raise ValueError('File limit exceeded; narrow audit scope')
        yield path


def classify(path: str, content: str) -> dict[str, list[str]]:
    # Names are evidence of implementation candidates, NOT verified operational readiness.
    name = path.lower()
    text = content.lower()[:MAX_SIZE]
    out = {}
    for category, patterns in CATEGORIES.items():
        filename_hits = [p for p in patterns if re.search(p, name)]
        content_hits = [p for p in patterns if re.search(p, text)]
        if filename_hits or content_hits:
            out[category] = ['path' if filename_hits else 'content']
    return out


def audit(root: Path, output: Path | None = None) -> tuple[dict, Path]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError('Project root does not exist')
    inventory = []
    for path in source_files(root):
        rel = path.relative_to(root).as_posix()
        # Exclude the audit itself to prevent self-inflated evidence.
        if rel.startswith('research/p0_s8/s8_22_10_26/') or rel == 'tests/test_s8221026_readiness.py':
            continue
        data = path.read_bytes()
        content = data.decode('utf-8-sig', errors='replace')
        categories = classify(rel, content)
        if categories:
            inventory.append({'path': rel, 'sha256': sha256(data), 'categories': sorted(categories), 'signals': categories})
    by_category = {key: sorted([x['path'] for x in inventory if key in x['categories']]) for key in CATEGORIES}
    # An intentionally separate evidence ledger: static discovery cannot promote any gate.
    gates = {key: {'status': 'NOT_VERIFIED', 'candidate_file_count': len(files), 'note': 'Static code references only; requires runtime, provenance and chronological validation'} for key, files in by_category.items()}
    report = {
        'milestone': MILESTONE, 'generated_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'audit_method': 'READ_ONLY_STATIC_REPOSITORY_INVENTORY',
        'inventory_file_count': len(inventory), 'categories': gates,
        'source_inventory': inventory,
        'readiness': {'historical_data_gate': 'NOT_VERIFIED', 'current_season_data_gate': 'NOT_VERIFIED',
                      'model_oos_gate': 'NOT_VERIFIED', 'market_odds_gate': 'NOT_VERIFIED',
                      'paper_ticket_pipeline_gate': 'NOT_VERIFIED', 'real_money_approval': 'DENIED'},
        'known_prior_evidence_user_reported': {
            '2023_11_15_espn_games': 8, '2023_11_15_espn_listings': 212,
            'adjacent_games': 29, 'adjacent_listings': 754,
            'candidate_players': 44, 'historical_team_certified': 0,
            'note': 'Reported from previous local runs; not independently re-verified by this inventory'},
        'research_status': 'RESEARCH_ONLY', 'training_decision': 'BLOCK_TRAINING',
        'recommendation': 'Inspect candidate files and validate live current-season inputs, chronological out-of-sample predictions, odds timestamps, calibration and ticket accounting before any betting authorization.',
    }
    output = output or (root / 'research/p0_s8/s8_22_10_26/results/opening_week_readiness.json')
    output = output.resolve()
    if not output.is_relative_to(root):
        raise ValueError('Output must remain within project root')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    csv_path = output.with_suffix('.csv')
    with csv_path.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(['category', 'candidate_file_count', 'status', 'example_files'])
        for category, paths in by_category.items():
            writer.writerow([category, len(paths), 'NOT_VERIFIED', '; '.join(paths[:8])])
    return report, output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', default='.')
    args = parser.parse_args()
    try:
        report, output = audit(Path(args.project_root))
    except (OSError, ValueError) as exc:
        parser.exit(2, 'FAIL CLOSED: ' + str(exc) + '\n')
    print('REPORT:', output)
    print('CSV:', output.with_suffix('.csv'))
    print(json.dumps({'inventory_file_count': report['inventory_file_count'],
                      'candidate_counts': {k: v['candidate_file_count'] for k, v in report['categories'].items()},
                      'readiness': report['readiness'], 'training_decision': report['training_decision']}, indent=2))


if __name__ == '__main__':
    main()
