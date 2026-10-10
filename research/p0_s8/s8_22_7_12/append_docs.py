"""Idempotently append S8.22.7.12 handoff/journal checkpoint, preserving backups."""
import argparse
from pathlib import Path
from shutil import copy2
from datetime import datetime,timezone
MARK='<!-- S8.22.7.12 documentation checkpoint -->'
TEXT={
 'DEVELOPMENT_JOURNAL.md':'''## S8.22.7.12 — Independent schedule-source acquisition

Goal: acquire and archive original bytes from a separate third-party date-level NBA schedule listing and compare all eight 2023-11-15 matchups offline. Candidate: SportsGamesToday date-specific TV listing. New source does not prove contemporaneous publication, upstream independence, or exhaustive slate. Source receipt and SHA256 produced only after actual manual acquisition. RESEARCH_ONLY / BLOCK_TRAINING.
''',
 'NEXT_AGENT_HANDOFF.md':'''## S8.22.7.12 handoff

Offline source-intake runner: `research/p0_s8/s8_22_7_12/run_s8_22_7_12.py`. Source must be manually acquired, then archived with actual retrieval UTC and SHA256. Review report before making any completeness claim. Even 8/8 matching games means candidate corroboration only; historical as-of and training blocked. Do not make automatic requests or stage evidence indiscriminately.
'''
}
def main():
 p=argparse.ArgumentParser();p.add_argument('--project-root',required=True);a=p.parse_args()
 for name,body in TEXT.items():
  target=Path(a.project_root)/'docs'/name
  if not target.exists():raise SystemExit(f'Missing {target}; not creating replacement')
  current=target.read_text(encoding='utf-8')
  if MARK in current: print(name,'ALREADY_PRESENT');continue
  backup=target.with_name(target.name+'.bak_s822712_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
  copy2(target,backup)
  target.write_text(current.rstrip()+'\n\n'+MARK+'\n'+body,encoding='utf-8')
  print(name,'APPENDED_WITH_BACKUP',backup)
if __name__=='__main__':main()
