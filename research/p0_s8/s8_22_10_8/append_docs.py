import argparse
from pathlib import Path
NOTE='\n### S8.22.10.8 — Game-ID evidence intake and safe Git inventory\nAdded SHA256-validated source snapshot intake, fail-closed provisional game-ID checks, and read-only Git inventory. No game IDs or player records certified; RESEARCH_ONLY / BLOCK_TRAINING.\n'
p=argparse.ArgumentParser();p.add_argument('--project-root',default='.')
root=Path(p.parse_args().project_root)
for name in ('DEVELOPMENT_JOURNAL.md','NEXT_AGENT_HANDOFF.md'):
    f=root/'docs'/name
    if not f.is_file():raise FileNotFoundError(f)
    old=f.read_text(encoding='utf-8')
    if '### S8.22.10.8 — Game-ID evidence intake' not in old:
        f.write_text(old.rstrip()+'\n'+NOTE,encoding='utf-8');print('UPDATED:',f)
    else:print('CHECKED:',f)
