"""Idempotent documentation checkpoint; backup original docs before changes."""
import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path
MARKER='<!-- S8.22.8 documentation checkpoint -->'
ENTRY='\n\n'+MARKER+'\n## S8.22.8 — Historical pregame feasibility audit\n\nAdded offline five-category evidence manifest and fail-closed feasibility report. Categories: player availability, expected minutes, starting lineups, player opportunity, betting markets. Historical as-of, licensing, and pre-tipoff evidence are unverified until independently substantiated. No source requests or model training. Decision: RESEARCH_ONLY / BLOCK_TRAINING. Next: manually review a permitted, historically timestamped source.\n'
def update(root):
    paths=[root/'docs/DEVELOPMENT_JOURNAL.md',root/'docs/NEXT_AGENT_HANDOFF.md']
    for p in paths:
        if not p.is_file(): raise FileNotFoundError(f'Existing document missing: {p}')
    for p in paths:
        old=p.read_text(encoding='utf-8-sig')
        if MARKER in old: print(p.name,'ALREADY_UPDATED');continue
        backup=p.with_name(p.name+'.bak_s8228_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
        shutil.copy2(p,backup);p.write_text(old+ENTRY,encoding='utf-8');print(p.name,'APPENDED_WITH_BACKUP',backup)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--project-root',default='.');args=a.parse_args();update(Path(args.project_root).resolve())
