"""Rerun S8.22.10.30-32 tests, then idempotently close out documentation."""
from pathlib import Path
import argparse
import subprocess
import sys

MARKER = '<!-- NBA_MIKE_S8_22_10_32_CLOSEOUT -->'
ENTRIES = {
 'DEVELOPMENT_JOURNAL.md': '''## S8.22.10.32 — Verified regression closeout
- User-run Windows Python 3.13.15: six regression tests passed; 25/25 combined S8.22.10.30–32 tests passed.
- Coverage: real canonical builder into adapter, prior-only opportunity features, deterministic repeat execution, artifact/manifest tamper rejection, and same-day isolation.
- S8.22.10.32 closeout reran combined suites successfully before documentation updates.
- No historical as-of source certification or out-of-sample predictive validation established. RESEARCH_ONLY / BLOCK_TRAINING / REAL-MONEY DENIED.
''',
 'NEXT_AGENT_HANDOFF.md': '''## S8.22.10.32 — Verified regression handoff
- Six regression tests and 25 combined synthetic tests passed in user's Windows environment; closeout reruns all three suites.
- Canonical → adapter → opportunity-feature contract and tamper defenses verified on synthetic fixtures only.
- Next: historical as-of evidence certification and source availability audit. No model training or betting approval.
''',
 'DISCOVERY_JOURNAL.md': '''## S8.22.10.32 — Engineering validation (not a predictive discovery)
- 6/6 regression and 25/25 combined synthetic tests passed in user-run Windows environment; closeout reverified.
- No accepted new basketball pattern or betting edge; historical as-of evidence remains uncertified.
''',
}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--project-root', type=Path, default=Path('.'))
    p.add_argument('--verify-only', action='store_true')
    a = p.parse_args()
    root = a.project_root.resolve()
    tests = [f'tests/test_s82210{i}_{suffix}.py' for i, suffix in [(30, 'integration'), (31, 'adapter'), (32, 'regression')]]
    if not (root / 'pyproject.toml').is_file() or any(not (root / t).is_file() for t in tests):
        p.error('Project root or required tests missing')
    result = subprocess.run([sys.executable, '-m', 'pytest', *tests, '-q', '-p', 'no:cacheprovider'], cwd=root, check=False)
    if result.returncode:
        print('Tests failed: no journals updated.', file=sys.stderr)
        return result.returncode
    if a.verify_only:
        print('Verification passed; journals untouched.')
        return 0
    paths = [(root / 'docs' / name, body) for name, body in ENTRIES.items()]
    if any(not path.is_file() for path, _ in paths):
        print('Required journal missing: no journals updated.', file=sys.stderr)
        return 2
    for path, body in paths:
        content = path.read_text(encoding='utf-8')
        if MARKER in content:
            print('ALREADY_PRESENT:', path)
            continue
        path.write_text(content.rstrip() + '\n\n' + MARKER + '\n' + body.rstrip() + '\n', encoding='utf-8', newline='\n')
        print('APPENDED:', path)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
