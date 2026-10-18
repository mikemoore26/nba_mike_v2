"""Append a verified, non-certifying milestone entry to existing docs."""
import argparse,json
from pathlib import Path

def run(root):
    root=Path(root).resolve()
    matches=list((root/'research/p0_s8/s8_22_10_23/results/2023-11-15').glob('*/review.json'))
    if len(matches)!=1:raise ValueError(f'Expected exactly one S8.22.10.23 review, got {len(matches)}')
    m=json.loads(matches[0].read_text(encoding='utf-8'))
    if m.get('milestone')!='S8.22.10.23' or m.get('training_decision')!='BLOCK_TRAINING' or m.get('historical_team_verified')!=0:raise ValueError('Governance mismatch')
    line='\n### S8.22.10.23 — Historical team evidence intake\n'+f"- Review: `{matches[0].relative_to(root)}`; classifications: `{json.dumps(m['classification_counts'],sort_keys=True)}`.\n- Dated evidence imported: "+str(m['evidence_rows'])+" rows; no identity, team, injury or as-of certification. `RESEARCH_ONLY / BLOCK_TRAINING`.\n"
    for name in ('DEVELOPMENT_JOURNAL.md','NEXT_AGENT_HANDOFF.md'):
        path=root/'docs'/name
        if not path.exists():raise ValueError('Missing existing doc: '+str(path))
        old=path.read_text(encoding='utf-8')
        if '### S8.22.10.23 — Historical team evidence intake' in old:print('UNCHANGED:',path);continue
        path.write_text(old.rstrip()+'\n'+line,encoding='utf-8');print('UPDATED:',path)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args()
    try:run(a.project_root)
    except (OSError,ValueError,KeyError,json.JSONDecodeError) as e:p.exit(2,'FAIL CLOSED: '+str(e)+'\n')
