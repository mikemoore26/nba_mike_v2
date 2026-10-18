"""Append S8.22.10.20 audit outcome only after successful run; idempotent."""
import argparse,json
from pathlib import Path
MARKER='<!-- S8.22.10.20 PLAYER REGISTRY RECONCILIATION -->'
def update(root):
    paths=sorted((root/'research/p0_s8/s8_22_10_20/results/2023-11-15').glob('*/review.json'))
    if not paths:raise ValueError('No S8.22.10.20 report found')
    reports=[json.loads(p.read_text(encoding='utf-8')) for p in paths]
    if any(r.get('training_decision')!='BLOCK_TRAINING' or r.get('player_candidates')!=44 for r in reports):raise ValueError('Invalid report')
    r=reports[-1]
    note=(f'\n{MARKER}\n### S8.22.10.20 — Player registry reconciliation\n'
          f'- 44 locally corroborated player names; 10 team notices excluded.\n'
          f'- Registry supplied: `{r["registry_supplied"]}`; candidate IDs proposed: `{r["candidate_ids_proposed"]}`.\n'
          f'- Classification: `{r["classification_counts"]}`.\n'
          f'- Evidence hashes: `{r["source_hashes"]}`.\n'
          f'- No independent identity, injury status or historical-as-of certification. `RESEARCH_ONLY / BLOCK_TRAINING`.\n')
    for rel in ('docs/DEVELOPMENT_JOURNAL.md','docs/NEXT_AGENT_HANDOFF.md'):
        p=root/rel
        if not p.is_file():raise FileNotFoundError(p)
        original=p.read_text(encoding='utf-8')
        if MARKER in original:print('UNCHANGED:',rel);continue
        p.write_text(original.rstrip()+'\n'+note,encoding='utf-8');print('UPDATED:',rel)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--project-root',default='.');x=a.parse_args();update(Path(x.project_root).resolve())
