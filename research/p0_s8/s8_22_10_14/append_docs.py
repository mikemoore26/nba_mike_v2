"""Idempotent milestone note; only after successful triage report."""
import argparse
import json
from pathlib import Path

MARKER='S8.22.10.14 INJURY LEDGER AUTOMATED TRIAGE'

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args();root=Path(a.project_root).resolve()
    reports=list((root/'research/p0_s8/s8_22_10_14/results/2023-11-15').glob('*/review.json'))
    if not reports: raise FileNotFoundError('Run S8.22.10.14 first')
    latest=max(reports,key=lambda x:x.stat().st_mtime);report=json.loads(latest.read_text(encoding='utf-8'))
    if report.get('milestone')!='S8.22.10.14' or report.get('training_decision')!='BLOCK_TRAINING':raise ValueError('Unexpected report')
    paragraph=(f'\n## {MARKER}\n'
      f'- Report: `{latest.relative_to(root).as_posix()}`.\n'
      f'- Original records: {report["records_total"]}; triage counts: {report["triage_counts"]}.\n'
      f'- Record types: {report["record_type_counts"]}.\n'
      '- Game-ID linkage is automated evidence only; injury statuses, player identity, and historical publication times remain NOT_CERTIFIED.\n'
      '- Exception queue and full row-level triage retained for follow-up; no invented human approvals or missing timestamps.\n'
      '- Governance: RESEARCH_ONLY / BLOCK_TRAINING.\n')
    targets=[root/'docs/DEVELOPMENT_JOURNAL.md',root/'docs/NEXT_AGENT_HANDOFF.md']
    if any(not t.is_file() for t in targets):raise FileNotFoundError('Journal/handoff missing')
    for path in targets:
        original=path.read_text(encoding='utf-8')
        if MARKER in original:print('ALREADY DOCUMENTED:',path.name);continue
        with path.open('a',encoding='utf-8') as f:f.write(paragraph)
        print('UPDATED:',path.name)
if __name__=='__main__':main()
