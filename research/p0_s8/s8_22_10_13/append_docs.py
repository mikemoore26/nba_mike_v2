"""Append an idempotent S8.22.10.13 journal/handoff checkpoint after run."""
import argparse
import json
from pathlib import Path

MARKER='S8.22.10.13 AUTOMATED GAME-ID EVIDENCE VERIFICATION'

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');args=p.parse_args()
    root=Path(args.project_root).resolve()
    results=list((root/'research/p0_s8/s8_22_10_13/results/2023-11-15').glob('*/review.json'))
    if not results: raise FileNotFoundError('Run S8.22.10.13 first')
    latest=max(results,key=lambda p:p.stat().st_mtime)
    report=json.loads(latest.read_text(encoding='utf-8'))
    paragraph=(f'\n## {MARKER}\n'
        f'- Report: `{latest.relative_to(root).as_posix()}`.\n'
        f'- Automated verified: {report["automated_verified"]}/{report["target_games"]}; exceptions: {report["manual_exceptions"]}.\n'
        f'- Crosswalk: SHA256 `{report["crosswalk_sha256"]}`; resolved from actual S8.22.10.7 output rather than an assumed folder token.\n'
        '- Automated evidence checks are not independent human certification, publisher authentication, or historical as-of proof.\n'
        '- Historical as-of and player identity: NOT_CERTIFIED; injury reviews: 0; governance: RESEARCH_ONLY / BLOCK_TRAINING.\n')
    for rel in ('docs/DEVELOPMENT_JOURNAL.md','docs/NEXT_AGENT_HANDOFF.md'):
        path=root/rel
        if not path.is_file(): raise FileNotFoundError(path)
        original=path.read_text(encoding='utf-8')
        if MARKER in original: print('ALREADY DOCUMENTED:',rel);continue
        with path.open('a',encoding='utf-8') as f:f.write(paragraph)
        print('UPDATED:',rel)

if __name__=='__main__':main()
