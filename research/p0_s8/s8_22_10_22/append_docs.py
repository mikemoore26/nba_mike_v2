"""Append verified local milestone status only; never claim certification."""
import argparse
import json
from pathlib import Path

def run(root):
    root=Path(root).resolve()
    base=root/'research/p0_s8/s8_22_10_22/results/2023-11-15'
    manifests=sorted(base.glob('*/capture_manifest.json')) if base.is_dir() else []
    if not manifests:
        raise ValueError('No validated fallback capture found; do not update docs')
    valid=[]
    import hashlib
    for file in manifests:
        data=json.loads(file.read_text(encoding='utf-8'))
        raw=file.parent/'nba_api_players_raw.json'
        if raw.exists() and hashlib.sha256(raw.read_bytes()).hexdigest()==data.get('raw_sha256') and data.get('training_decision')=='BLOCK_TRAINING':
            valid.append((file,data))
    if not valid:raise ValueError('No hash-valid fallback capture found')
    file,data=valid[-1]
    marker='S8.22.10.22'
    paragraph=(f'\n### {marker} — third-party registry acquisition\n'
               f'- Captured {data["players_count"]} name/ID entries; raw SHA256 `{data["raw_sha256"]}`.\n'
               f'- Evidence: `{file.relative_to(root).as_posix()}`; capture mode `{data["capture_mode"]}`.\n'
               '- Third-party candidate evidence only; historical team, identity certification, injury status and as-of all unverified.\n'
               '- Governance: `RESEARCH_ONLY / BLOCK_TRAINING`.\n')
    for name in ['DEVELOPMENT_JOURNAL.md','NEXT_AGENT_HANDOFF.md']:
        path=root/'docs'/name
        if not path.is_file():raise ValueError(f'Missing {path}')
        existing=path.read_text(encoding='utf-8')
        if marker not in existing:
            path.write_text(existing.rstrip()+'\n'+paragraph,encoding='utf-8')
            print('UPDATED:',path.relative_to(root))
        else:print('ALREADY RECORDED:',path.relative_to(root))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args()
    try:run(a.project_root)
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as e:p.exit(2,'FAIL CLOSED: '+str(e)+'\n')
