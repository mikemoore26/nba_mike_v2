"""Append a reproducible S8.22.10 checkpoint, with backups, without replacing existing docs."""
import argparse
import shutil
from datetime import datetime,timezone
from pathlib import Path
MARK='<!-- S8.22.10 documentation checkpoint -->'
ENTRY='''\n\n<!-- S8.22.10 documentation checkpoint -->
## S8.22.10 — Historical official injury PDF pilot

Implemented manual-only official NBA PDF intake with SHA256 archive, embedded edition-label extraction, eight November 15, 2023 tipoffs, and 60-minute cutoff comparison. The PDF edition label is NOT proof of historical public availability. No network calls, automatic retries, player eligibility claims, training, or production approval. Pilot requires an actual manually obtained original PDF before it can produce evidence. Decision: RESEARCH_ONLY / BLOCK_TRAINING.\n'''
def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');args=p.parse_args()
    root=Path(args.project_root).resolve()
    targets=[root/'docs/DEVELOPMENT_JOURNAL.md',root/'docs/NEXT_AGENT_HANDOFF.md']
    for t in targets:
        if not t.is_file():raise SystemExit(f'Missing existing document: {t}')
    for t in targets:
        text=t.read_text(encoding='utf-8')
        if MARK in text:
            print(t.name,'ALREADY_PRESENT');continue
        backup=t.with_name(t.name+'.bak_s82210_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
        shutil.copy2(t,backup)
        with t.open('a',encoding='utf-8',newline='\n') as f:f.write(ENTRY)
        print(t.name,'APPENDED_WITH_BACKUP',backup)
if __name__=='__main__':main()
