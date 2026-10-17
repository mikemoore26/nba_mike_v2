from pathlib import Path
import argparse
p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args();root=Path(a.project_root)
for name in ('DEVELOPMENT_JOURNAL.md','NEXT_AGENT_HANDOFF.md'):
 f=root/'docs'/name
 if not f.exists():raise FileNotFoundError(f)
 marker='S8.22.10.9 — NBA CDN game source acquisition'
 content=f.read_text(encoding='utf-8')
 if marker not in content:
  with f.open('a',encoding='utf-8') as out:out.write('\n\n## '+marker+'\nAdded a fail-closed historical NBA CDN JSON acquisition and SHA256 receipt workflow for eight provisional game IDs. Source content checks do not independently certify game IDs or historical as-of. Manual player reviews remain pending; RESEARCH_ONLY / BLOCK_TRAINING. See docs/S8_22_10_9_SOURCE_ACQUISITION.md.\n')
 print('CHECKED:',f)
