"""Append S8.22.10.32 notes after successful repository tests; no missing-file creation."""
from __future__ import annotations
import argparse
from pathlib import Path

MARKER = '<!-- NBA_MIKE_S8_22_10_32 -->'
ENTRIES = {
    'DEVELOPMENT_JOURNAL.md': '''## S8.22.10.32 — Adapter integration and regression audit
- Previous S8.22.10.31: 12/12 tests passed in Windows; commit `0bd98c2` pushed to main.
- Added cross-module synthetic regression tests: canonical builder -> canonical-to-D-1 adapter -> opportunity research features.
- Test coverage: historical cutoff, expected entity history, repeatability, artifact hash, manifest row count, same-day leakage.
- Confirmed `target_minutes` is an evaluation label and must be stripped before any pregame prediction.
- Local isolated test result: 6/6 passed; Windows repository result must be independently verified before declaring milestone complete.
- Status: RESEARCH_ONLY / BLOCK_TRAINING / REAL-MONEY DENIED. No historical as-of source certification or OOS betting validation.
''',
    'NEXT_AGENT_HANDOFF.md': '''## Latest milestone — S8.22.10.32
S8.22.10.31 passed 12/12 Windows tests, committed `0bd98c2`. S8.22.10.32 introduces `tests/test_s8221032_regression.py` for real canonical builder -> adapter -> opportunity feature flow, with 6 isolated local passes; verify in user's Windows repository. Snapshot D-1 date exclusion is not historical publication/as-of certification. Opportunity research output contains `target_minutes` (evaluation-only). Keep RESEARCH_ONLY / BLOCK_TRAINING / REAL-MONEY DENIED. Next: review Windows test result, then as-of provenance certification and safe feature-only interface.
''',
}


def update(path: Path, body: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f'Required existing journal missing: {path}')
    original=path.read_text(encoding='utf-8')
    if MARKER in original:
        return 'ALREADY_PRESENT'
    # Exactly one blank line before marker and exactly one terminal newline.
    content=original.rstrip()+'\n\n'+MARKER+'\n'+body.rstrip()+'\n'
    path.write_text(content,encoding='utf-8',newline='\n')
    return 'APPENDED'


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--project-root',type=Path,default=Path('.'))
    args=parser.parse_args()
    docs=args.project_root.resolve()/'docs'
    for name in ENTRIES:
        if not (docs/name).is_file():
            raise SystemExit(f'ABORT: missing required journal: {docs/name}')
    for name,body in ENTRIES.items():
        print(f'{update(docs/name,body)}: {docs/name}')

if __name__=='__main__':
    main()
