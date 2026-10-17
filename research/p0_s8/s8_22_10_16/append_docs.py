"""Append an idempotent milestone summary only after successful S8.22.10.16 run."""
import argparse
import json
from pathlib import Path

MARKER='S8.22.10.16 DATE-AWARE TEAM NOTICE CLASSIFICATION'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project-root',default='.')
    args=parser.parse_args()
    root=Path(args.project_root).resolve()
    reports=list((root/'research/p0_s8/s8_22_10_16/results/2023-11-15').glob('*/review.json'))
    if len(reports)!=1: raise ValueError('Expected exactly one S8.22.10.16 report')
    report=json.loads(reports[0].read_text(encoding='utf-8'))
    if report.get('milestone')!='S8.22.10.16' or report.get('training_decision')!='BLOCK_TRAINING' or report.get('records_classified')!=4:
        raise ValueError('Invalid S8.22.10.16 report')
    entry=(f'\n## {MARKER}\n'
           f'- Report: `{reports[0].relative_to(root).as_posix()}`.\n'
           f'- Four team-submission notices classified; outcomes: {report["classification_counts"]}.\n'
           '- No corrected game dates, new verified game IDs, injury certifications, or original-ledger edits.\n'
           '- Next: independent PDF/date provenance for notices; player identity and as-of evidence for 44 player candidates.\n'
           '- Governance: RESEARCH_ONLY / BLOCK_TRAINING.\n')
    for relative in ('docs/DEVELOPMENT_JOURNAL.md','docs/NEXT_AGENT_HANDOFF.md'):
        path=root/relative
        if not path.is_file(): raise FileNotFoundError(path)
        if MARKER in path.read_text(encoding='utf-8'):
            print('ALREADY DOCUMENTED:',relative); continue
        with path.open('a',encoding='utf-8') as stream: stream.write(entry)
        print('UPDATED:',relative)

if __name__=='__main__': main()
