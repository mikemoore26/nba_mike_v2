"""Idempotent S8.22.10.19 milestone documentation."""
import argparse,json
from pathlib import Path
MARKER='<!-- S8.22.10.19 COORDINATE NAME REPAIR -->'
def update(root):
    reports=list((root/'research/p0_s8/s8_22_10_19/results/2023-11-15').glob('*/review.json'))
    if len(reports)!=1:raise ValueError(f'Expected one report, got {len(reports)}')
    r=json.loads(reports[0].read_text(encoding='utf-8'))
    if r.get('training_decision')!='BLOCK_TRAINING' or r.get('player_rows')!=44:raise ValueError('Invalid report')
    note=f'\n{MARKER}\n### S8.22.10.19 — Coordinate-aware name comparison\n- 44 player candidates evaluated, 10 team notices excluded.\n- Local matches: {r["locally_corrob"]}; unmatched: {r["unmatched"]}; classes: `{r["match_counts"]}`.\n- Original ledger SHA-256: `{r["source_ledger_sha256"]}`.\n- Source diagnostic SHA-256: `{r["source_diagnostic_sha256"]}`.\n- Local name matches are NOT independently verified player IDs, injury statuses, or historical publication timestamps.\n- Governance: `RESEARCH_ONLY / BLOCK_TRAINING`.\n'
    for rel in ('docs/DEVELOPMENT_JOURNAL.md','docs/NEXT_AGENT_HANDOFF.md'):
        p=root/rel
        if not p.is_file():raise FileNotFoundError(p)
        old=p.read_text(encoding='utf-8')
        if MARKER in old:print('UNCHANGED:',rel);continue
        p.write_text(old.rstrip()+'\n'+note,encoding='utf-8');print('UPDATED:',rel)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args();update(Path(a.project_root).resolve())
