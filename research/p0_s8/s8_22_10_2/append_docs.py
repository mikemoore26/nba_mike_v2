"""Idempotently append S8.22.10.2 research milestone to existing journal and handoff."""
import argparse
from pathlib import Path

MARKER='## S8.22.10.2 — Coordinate-aware injury candidate attribution'
TEXT=f'''\n{MARKER}\n- Implemented offline coordinate-aware candidate extraction from the archived 2023-11-15 NBA injury PDF; player rows and team-level NOT YET SUBMITTED notices are separate.\n- SHA256/receipt verification, page and coordinate provenance, conservative game/team matching, ambiguity flags, manual review required.\n- Runtime dependency: pypdf; test dependency: pytest. Previous S8.22.10.1 tests additionally require reportlab.\n- Outputs remain local; do not stage raw PDFs or generated result files.\n- Governance: RESEARCH_ONLY / BLOCK_TRAINING; historical as-of NOT_CERTIFIED.\n- Next: inspect actual candidate CSV and ambiguities against original PDF pages before certifying extraction quality.\n'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args()
    root=Path(a.project_root).resolve()
    for rel in ['docs/DEVELOPMENT_JOURNAL.md','docs/NEXT_AGENT_HANDOFF.md']:
        path=root/rel
        if not path.is_file():raise FileNotFoundError(f'Required document missing: {path}')
        original=path.read_text(encoding='utf-8')
        if MARKER not in original:
            path.write_text(original.rstrip()+'\n'+TEXT,encoding='utf-8')
            print('UPDATED:',path)
        else:print('ALREADY DOCUMENTED:',path)
if __name__=='__main__':main()
