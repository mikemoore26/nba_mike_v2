"""Append an accurate S8.22.10.11 handoff entry after inspecting results."""
import argparse
from pathlib import Path
import json
p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args();root=Path(a.project_root)
reports=list((root/'research/p0_s8/s8_22_10_11/results/2023-11-15').glob('*/review.json'))
if len(reports)!=1:raise RuntimeError('Expected one S8.22.10.11 report')
report=json.loads(reports[0].read_text(encoding='utf-8'))
marker='S8.22.10.11 — independent schedule-link discovery'
line=f"Schedule acquisition={report['schedule_acquisition']}; discovery={report['discovery_counts']}; evidence={report['evidence_counts']}; certified IDs=0; as-of NOT_CERTIFIED; RESEARCH_ONLY / BLOCK_TRAINING. Source report: {reports[0].relative_to(root)}."
for name in ('DEVELOPMENT_JOURNAL.md','NEXT_AGENT_HANDOFF.md'):
 path=root/'docs'/name
 if not path.exists():raise FileNotFoundError(path)
 content=path.read_text(encoding='utf-8')
 if marker not in content:
  with path.open('a',encoding='utf-8') as f:f.write('\n\n## '+marker+'\n'+line+'\n')
 print('CHECKED:',path)
