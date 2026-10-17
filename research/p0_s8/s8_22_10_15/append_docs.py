"""Append an idempotent, evidence-grounded milestone entry after successful run."""
import argparse
import json
from pathlib import Path
MARKER='S8.22.10.15 MAPPING EXCEPTION DIAGNOSIS'
def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args();root=Path(a.project_root).resolve()
    reports=list((root/'research/p0_s8/s8_22_10_15/results/2023-11-15').glob('*/review.json'))
    if len(reports)!=1:raise ValueError('Expected exactly one S8.22.10.15 report')
    report=json.loads(reports[0].read_text(encoding='utf-8'))
    if report.get('milestone')!='S8.22.10.15' or report.get('training_decision')!='BLOCK_TRAINING':raise ValueError('Invalid report')
    note=(f'\n## {MARKER}\n- Report: `{reports[0].relative_to(root).as_posix()}`.\n'
          f'- Exceptions analyzed: {report["mapping_exceptions_analyzed"]}; outcomes: {report["resolution_counts"]}; reasons: {report["reason_counts"]}.\n'
          '- No original ledger changes, no injury certifications, no fabricated publication timestamps.\n'
          '- Next: inspect deterministic candidates versus unresolved conflicts; preserve provenance and as-of gates.\n'
          '- Governance: RESEARCH_ONLY / BLOCK_TRAINING.\n')
    targets=[root/'docs/DEVELOPMENT_JOURNAL.md',root/'docs/NEXT_AGENT_HANDOFF.md']
    if any(not t.is_file() for t in targets):raise FileNotFoundError('Missing documentation')
    for t in targets:
        if MARKER in t.read_text(encoding='utf-8'):print('ALREADY DOCUMENTED:',t.name);continue
        with t.open('a',encoding='utf-8') as f:f.write(note)
        print('UPDATED:',t.name)
if __name__=='__main__':main()
