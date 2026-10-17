"""Append S8.22.10.17 milestone note to journal and handoff, idempotently."""
import argparse
from pathlib import Path
import json

MARKER='<!-- S8.22.10.17 PLAYER EVIDENCE AUDIT -->'

def update(root):
    base=root/'research/p0_s8/s8_22_10_17/results/2023-11-15'
    reports=sorted(base.glob('*/review.json'))
    if len(reports)!=1: raise ValueError(f'Expected exactly one S8.22.10.17 report, found {len(reports)}')
    report=json.loads(reports[0].read_text(encoding='utf-8'))
    if report.get('milestone')!='S8.22.10.17' or report.get('training_decision')!='BLOCK_TRAINING' or report.get('player_candidates')!=44: raise ValueError('Unexpected report/governance')
    note=f'\n{MARKER}\n### S8.22.10.17 — Player identity / injury evidence inventory\n- 44 player candidates audited; 10 team-submission notices excluded.\n- Dispositions: {report["disposition_counts"]}.\n- Source ledger SHA-256: `{report["source_ledger_sha256"]}`.\n- Source triage SHA-256: `{report["source_triage_sha256"]}`.\n- No independent player ID, injury status, or historical publication-time certifications.\n- Research governance: `RESEARCH_ONLY / BLOCK_TRAINING`.\n- Next: acquire authoritative timestamped source evidence; do not promote parser candidates.\n'
    for rel in ('docs/DEVELOPMENT_JOURNAL.md','docs/NEXT_AGENT_HANDOFF.md'):
        path=root/rel
        if not path.is_file(): raise FileNotFoundError(path)
        original=path.read_text(encoding='utf-8')
        if MARKER in original: print('UNCHANGED:',rel);continue
        path.write_text(original.rstrip()+'\n'+note,encoding='utf-8')
        print('UPDATED:',rel)

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args()
    update(Path(a.project_root).resolve())
if __name__=='__main__':main()
