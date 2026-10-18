"""Append milestone note only after a valid successful S8.22.10.21 capture."""
import argparse,json
from pathlib import Path

def run(root):
    root=root.resolve();captures=list((root/'research/p0_s8/s8_22_10_21/results/2023-24').glob('*/capture_manifest.json'))
    valid=[]
    for path in captures:
        try:
            m=json.loads(path.read_text(encoding='utf-8'))
            import hashlib
            raw=path.parent/'commonallplayers_raw.json'
            if raw.is_file() and hashlib.sha256(raw.read_bytes()).hexdigest()==m['raw_sha256'] and m['training_decision']=='BLOCK_TRAINING':valid.append((path,m))
        except (KeyError,ValueError):continue
    if not valid:raise ValueError('No validated registry capture found; do not update docs')
    path,m=sorted(valid,key=lambda p:p[1]['retrieved_at_utc'])[-1]
    marker='S8.22.10.21 — NBA registry acquisition'
    line=(f'\n### {marker}\n- Captured {m["registry_rows"]} registry rows ({m["unique_person_ids"]} distinct IDs) from {m["mode"]}; '
          f'raw SHA-256 `{m["raw_sha256"]}`; manifest `{path.relative_to(root).as_posix()}`. '
          'Source response is not independent historical team certification. Governance: RESEARCH_ONLY / BLOCK_TRAINING.\n')
    for name in ['DEVELOPMENT_JOURNAL.md','NEXT_AGENT_HANDOFF.md']:
        dest=root/'docs'/name
        if not dest.is_file():raise ValueError('Missing docs/'+name)
        text=dest.read_text(encoding='utf-8')
        if marker not in text:dest.write_text(text.rstrip()+'\n'+line,encoding='utf-8');print('UPDATED:',dest)
        else:print('ALREADY RECORDED:',dest)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project-root',type=Path,default=Path('.'));a=p.parse_args()
    try:run(a.project_root)
    except (ValueError,FileNotFoundError) as e:p.exit(2,'FAIL CLOSED: '+str(e)+'\n')
