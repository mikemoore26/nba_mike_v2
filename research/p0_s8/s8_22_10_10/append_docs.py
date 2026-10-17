"""Idempotent documentation update; append only, do not overwrite prior notes."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args();root=Path(a.project_root)
marker='S8.22.10.10 — NBA public game-page evidence intake'
for name in ('DEVELOPMENT_JOURNAL.md','NEXT_AGENT_HANDOFF.md'):
 f=root/'docs'/name
 if not f.exists():raise FileNotFoundError(f)
 content=f.read_text(encoding='utf-8')
 if marker not in content:
  with f.open('a',encoding='utf-8') as out:out.write('\n\n## '+marker+'\nAdded a fail-closed NBA public HTML game-page acquisition and immutable SHA256 evidence receipts for eight November 15, 2023 matchups. CDN returned HTTP 403 in prior step. Page title checks are only preliminary: game ID is present in requested URL and is NOT independently certified. Historical as-of and player review remain unresolved. RESEARCH_ONLY / BLOCK_TRAINING. See docs/S8_22_10_10_PUBLIC_GAME_PAGE_EVIDENCE.md.\n')
 print('CHECKED:',f)
