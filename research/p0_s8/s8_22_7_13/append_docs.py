"""Append milestone notes to existing docs with backup, without duplicating marker."""
import argparse
from datetime import datetime, timezone
from pathlib import Path

MARKER='<!-- S8.22.7.13 documentation checkpoint -->'
NOTE='''\n\n<!-- S8.22.7.13 documentation checkpoint -->
## S8.22.7.13 — Independent source governance review

**Goal:** Offline audit of S8.22.7.12 third-party source integrity and the limits of eight-game agreement.

**Decision:** Distinct publisher domain is observed, but upstream editorial independence, exhaustive date completeness, and 2023 pregame publication are not established. Keep `RESEARCH_ONLY / BLOCK_TRAINING`.

**Validation:** `python -m pytest tests/test_s822713_source_governance.py -q` and review local source-governance report. Source bytes are not modified or committed automatically.
'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',required=True);args=p.parse_args()
    root=Path(args.project_root).resolve()
    for name in ('DEVELOPMENT_JOURNAL.md','NEXT_AGENT_HANDOFF.md'):
        path=root/'docs'/name
        if not path.is_file(): raise SystemExit(f'Missing {path}; refusing to create replacement')
        text=path.read_text(encoding='utf-8')
        if MARKER in text: print(name,'ALREADY_PRESENT');continue
        backup=path.with_name(name+'.bak_s822713_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
        if backup.exists(): raise SystemExit(f'Backup collision: {backup}')
        backup.write_bytes(path.read_bytes())
        with path.open('a',encoding='utf-8',newline='') as f:f.write(NOTE)
        print(name,'APPENDED_WITH_BACKUP',backup)
if __name__=='__main__':main()
