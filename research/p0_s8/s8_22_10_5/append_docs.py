"""Append S8.22.10.5 status without claiming human verification."""
import argparse
from pathlib import Path

ENTRY='''\n## S8.22.10.5 — Manual evidence verification packet\n- Added PDF-anchored review ledger for S8.22.10.4 candidates and notices.\n- Explicitly flags prior-slate home/away orientation conflicts and potential column-header artifacts.\n- All candidate rows start PENDING; no automated player or as-of certification.\n- Governance: RESEARCH_ONLY / BLOCK_TRAINING.\n'''

def run(root):
    for name in ('docs/DEVELOPMENT_JOURNAL.md','docs/NEXT_AGENT_HANDOFF.md'):
        path=root/name
        if not path.is_file():raise FileNotFoundError(path)
        content=path.read_text(encoding='utf-8')
        if '## S8.22.10.5 — Manual evidence verification packet' not in content:
            path.write_text(content.rstrip()+'\n'+ENTRY,encoding='utf-8')
            print('UPDATED:',path)
        else:print('UNCHANGED:',path)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.')
    a=p.parse_args();run(Path(a.project_root).resolve())
