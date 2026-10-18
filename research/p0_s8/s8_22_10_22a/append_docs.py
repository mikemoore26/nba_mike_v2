"""Idempotent milestone documentation update after hash-validated local capture."""
import argparse,hashlib,json
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(root):
    root=Path(root).resolve();base=root/'research/p0_s8/s8_22_10_22a/results/2023-11-15'
    valid=[]
    for f in sorted(base.glob('*/capture_manifest.json')):
        m=json.loads(f.read_text(encoding='utf-8'))
        if m.get('training_decision')!='BLOCK_TRAINING' or m.get('milestone')!='S8.22.10.22A':continue
        expected={'installed_nba_api_players.json':'raw_sha256','third_party_name_only_adapter.json':'adapter_sha256','player_id_candidates.csv':'candidate_csv_sha256'}
        if all((f.parent/n).is_file() and sha(f.parent/n)==m.get(k) for n,k in expected.items()):valid.append((f,m))
    if len(valid)!=1:raise ValueError(f'Expected exactly one hash-validated local registry capture; got {len(valid)}')
    f,m=valid[0];marker='S8.22.10.22A — local nba_api registry integration'
    paragraph=(f'\n### {marker}\n- Local installed nba_api {m["source_provenance"]["package_version"]}: {m["raw_count"]} player records, SHA256 `{m["raw_sha256"]}`.\n- Name/ID candidates: {m["classification_counts"]}.\n- Evidence manifest: `{f.relative_to(root).as_posix()}`.\n- Local third-party names do not prove 2023 team membership or historical as-of. Player IDs certified: 0.\n- Governance: `RESEARCH_ONLY / BLOCK_TRAINING`.\n')
    for name in ('DEVELOPMENT_JOURNAL.md','NEXT_AGENT_HANDOFF.md'):
        path=root/'docs'/name
        if not path.is_file():raise ValueError('Missing documentation: '+str(path))
        s=path.read_text(encoding='utf-8')
        if marker not in s:path.write_text(s.rstrip()+'\n'+paragraph,encoding='utf-8');print('UPDATED:',path)
        else:print('ALREADY RECORDED:',path)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args()
    try:run(a.project_root)
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as e:p.exit(2,'FAIL CLOSED: '+str(e)+'\n')
