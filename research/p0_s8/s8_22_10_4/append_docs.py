"""Append S8.22.10.4 handoff and journal entries once, without modifying other text."""
import argparse
from pathlib import Path

MARKER='S8.22.10.4 — Date-aware injury PDF attribution'
ENTRY=f'''\n## {MARKER}\n- Corrected page-four y-coordinate coverage and game-date transitions; preserve 11/15 Lakers and classify 11/16 BKN@MIA / OKC@GSW outside the eight-game research slate.\n- Inputs: SHA256-verified archived injury PDF. Outputs: date-scoped candidate CSVs and ambiguity review. Five synthetic regression tests pass in patch environment; run against archived PDF locally and inspect results before promotion.\n- Manual table verification, player identity, publication as-of, DNP population and training gates remain unresolved. Status: RESEARCH_ONLY / BLOCK_TRAINING.\n'''

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project-root',default='.');a=parser.parse_args()
    root=Path(a.project_root).resolve()
    for rel in ('docs/DEVELOPMENT_JOURNAL.md','docs/NEXT_AGENT_HANDOFF.md'):
        p=root/rel
        if not p.is_file():raise FileNotFoundError(f'Required document missing: {p}')
        text=p.read_text(encoding='utf-8')
        if MARKER in text:print('ALREADY DOCUMENTED:',p);continue
        with p.open('a',encoding='utf-8',newline='\n') as f:f.write(ENTRY)
        print('UPDATED:',p)
if __name__=='__main__':main()
