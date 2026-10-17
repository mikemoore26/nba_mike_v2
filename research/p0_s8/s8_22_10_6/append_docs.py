import argparse,pathlib
p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args();root=pathlib.Path(a.project_root)
for name in ('DEVELOPMENT_JOURNAL.md','NEXT_AGENT_HANDOFF.md'):
 f=root/'docs'/name
 if not f.exists():raise SystemExit(f'Missing {f}')
 marker='S8.22.10.6 — independent schedule reconciliation'
 text=f.read_text(encoding='utf-8')
 if marker not in text:
  f.write_text(text.rstrip()+f'\n\n### {marker}\nCreated read-only date-aware external schedule crosswalk; manual player verification and historical as-of remain pending. RESEARCH_ONLY / BLOCK_TRAINING. See docs/S8_22_10_6_SCHEDULE_RECONCILIATION.md.\n',encoding='utf-8')
 print('CHECKED:',f)
