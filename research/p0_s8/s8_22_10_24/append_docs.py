"""Append S8.22.10.24 research findings after validated capture."""
import argparse,hashlib,json
from pathlib import Path

def run(root):
    root=Path(root).resolve();base=root/'research/p0_s8/s8_22_10_24/results/2023-11-15'
    matches=list(base.glob('*/review.json'))
    if len(matches)!=1:raise ValueError(f'Expected exactly one successful S8.22.10.24 capture; got {len(matches)}')
    path=matches[0];m=json.loads(path.read_text(encoding='utf-8'))
    if m.get('milestone')!='S8.22.10.24' or m.get('training_decision')!='BLOCK_TRAINING' or m.get('historical_team_verified')!=0 or m.get('player_candidates')!=44:raise ValueError('Governance mismatch')
    for e in m['evidence_documents']:
        p=path.parent/e['relative_path']
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=e['sha256']:raise ValueError('Evidence hash mismatch: '+str(p))
    for file,key in [('historical_team_boxscore_review.csv','review_csv_sha256'),('boxscore_listings.json','boxscore_listings_sha256')]:
        p=path.parent/file
        if hashlib.sha256(p.read_bytes()).hexdigest()!=m[key]:raise ValueError('Output hash mismatch: '+file)
    header='### S8.22.10.24 — Historical ESPN boxscore evidence capture'
    entry=f'\n{header}\n- Evidence report: `{path.relative_to(root)}`; {m["scoreboard_event_count"]} games; {m["raw_boxscore_listings"]} boxscore listings; 44 candidates.\n- Classifications: `{json.dumps(m["classification_counts"],sort_keys=True)}`. Third-party game-day evidence only; no roster, player ID, injury or publication-time certification. `RESEARCH_ONLY / BLOCK_TRAINING`.\n'
    paths=[root/'docs/DEVELOPMENT_JOURNAL.md',root/'docs/NEXT_AGENT_HANDOFF.md']
    if not all(p.is_file() for p in paths):raise ValueError('Missing project documentation')
    for p in paths:
        old=p.read_text(encoding='utf-8')
        if header in old:print('UNCHANGED:',p);continue
        p.write_text(old.rstrip()+'\n'+entry,encoding='utf-8');print('UPDATED:',p)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--project-root',default='.');args=parser.parse_args()
    try:run(args.project_root)
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as e:parser.exit(2,'FAIL CLOSED: '+str(e)+'\n')
