"""Idempotent milestone documentation after a successful S8.22.10.18 run."""
import argparse
from pathlib import Path
import json
MARKER='<!-- S8.22.10.18 NAME LAYOUT DIAGNOSTICS -->'
def update(root):
    reports=list((root/'research/p0_s8/s8_22_10_18/results/2023-11-15').glob('*/review.json'))
    if len(reports)!=1:raise ValueError(f'Expected one diagnostic report, got {len(reports)}')
    r=json.loads(reports[0].read_text(encoding='utf-8'))
    if r.get('training_decision')!='BLOCK_TRAINING' or r.get('player_rows')!=44:raise ValueError('Invalid diagnostic governance')
    note=f'\n{MARKER}\n### S8.22.10.18 — Uniform name diagnostic failure investigation\n- 44 candidate rows diagnosed; no original evidence modified.\n- Name-layout classifications: `{r["diagnostic_counts"]}`.\n- Ledger SHA-256: `{r["source_ledger_sha256"]}`.\n- Prior audit SHA-256: `{r["source_audit_sha256"]}`.\n- These are local text-layout diagnostics, not independent identity, injury-status, or historical-as-of certifications.\n- Governance: `RESEARCH_ONLY / BLOCK_TRAINING`.\n- Next: inspect classifications, then obtain authoritative player ID, injury status and publication-time evidence.\n'
    for rel in ('docs/DEVELOPMENT_JOURNAL.md','docs/NEXT_AGENT_HANDOFF.md'):
        p=root/rel
        if not p.is_file():raise FileNotFoundError(p)
        old=p.read_text(encoding='utf-8')
        if MARKER in old:print('UNCHANGED:',rel);continue
        p.write_text(old.rstrip()+'\n'+note,encoding='utf-8');print('UPDATED:',rel)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args();update(Path(a.project_root).resolve())
