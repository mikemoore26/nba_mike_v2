"""Idempotent append with backups; no source or existing doc replacement."""
import argparse
from datetime import datetime,timezone
from pathlib import Path

MARKER='<!-- S8.22.9 documentation checkpoint -->'
ENTRY='''\n\n<!-- S8.22.9 documentation checkpoint -->
## S8.22.9 — Historical pregame provider shortlist

Reviewed official NBA injury-report archive, SportsDataIO, BALLDONTLIE, and strictly lagged local game-log derivations. Provider descriptions and URLs are in `research/p0_s8/s8_22_9/source_candidates.json`. This is a source-discovery shortlist only; November 2023 as-of timestamps, licensing, and access are NOT_VERIFIED. Priority: manually examine dated official injury reports, ask commercial provider about 2023 replay and timestamps, then design a lag-only minutes/opportunity proof. No credentials, network calls, training, or routine collection. Decision: RESEARCH_ONLY / BLOCK_TRAINING.
'''
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--project-root',default='.');a=ap.parse_args()
    root=Path(a.project_root).resolve()
    paths=[root/'docs/DEVELOPMENT_JOURNAL.md',root/'docs/NEXT_AGENT_HANDOFF.md']
    for p in paths:
        if not p.is_file(): raise SystemExit(f'Missing required existing file: {p}')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for p in paths:
        old=p.read_text(encoding='utf-8')
        if MARKER in old: print(p.name,'ALREADY_PRESENT');continue
        backup=p.with_name(p.name+'.bak_s8229_'+stamp)
        backup.write_bytes(p.read_bytes())
        with p.open('a',encoding='utf-8',newline='\n') as f:f.write(ENTRY)
        print(p.name,'APPENDED_WITH_BACKUP',backup)
if __name__=='__main__':main()
