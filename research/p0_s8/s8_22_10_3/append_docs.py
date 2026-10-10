"""Append milestone record to project journal and handoff once (idempotent)."""
import argparse
from pathlib import Path

MARK='S8.22.10.3 — Cross-page injury candidate attribution'
ENTRY=f'''\n## {MARK}\n\n- Implemented offline coordinate-based PDF reconstruction with cross-page context, footer exclusion, team/matchup consistency checks, and out-of-slate classification.\n- Inputs: original S8.22.10 evidence receipt and SHA256-verified PDF. Outputs: research/p0_s8/s8_22_10_3/results/2023-11-15/<run-id>/ (not automatically committed).\n- Review page continuations, especially Toronto/Gary Trent Jr., Phoenix players, and page-4 Miami / OKC@GSW notices. Review all ambiguities and out-of-slate candidates against source PDF.\n- Scope is the independently corroborated eight-game research slate, NOT necessarily the entire NBA injury report.\n- No historical publication-time proof, player identity certification, eligibility, DNP labeling or model training. RESEARCH_ONLY / BLOCK_TRAINING.\n- Test-only dependency: reportlab (S8.22.10.1); this milestone's tests use no reportlab.\n'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args()
    root=Path(a.project_root).resolve()
    for relative in ('docs/DEVELOPMENT_JOURNAL.md','docs/NEXT_AGENT_HANDOFF.md'):
        path=root/relative
        if not path.is_file():raise SystemExit(f'Missing expected project document: {path}')
        old=path.read_text(encoding='utf-8')
        if MARK in old:print('ALREADY PRESENT:',path);continue
        with path.open('a',encoding='utf-8',newline='\n') as f:f.write(ENTRY)
        print('UPDATED:',path)
if __name__=='__main__':main()
