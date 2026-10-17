"""Append S8.22.10.7 milestone note once; does not claim real-world certification."""
import argparse
from pathlib import Path

NOTE = '\n### S8.22.10.7 — Provisional game-ID crosswalk and manual review staging\nPrepared non-destructive, date-aware game-ID hypotheses and human-review ledger. Game IDs remain unverified; all manual reviews pending; RESEARCH_ONLY / BLOCK_TRAINING.\n'


def main():
    p = argparse.ArgumentParser(); p.add_argument('--project-root', default='.')
    root = Path(p.parse_args().project_root)
    for name in ('DEVELOPMENT_JOURNAL.md', 'NEXT_AGENT_HANDOFF.md'):
        path = root / 'docs' / name
        if not path.exists():
            raise FileNotFoundError(path)
        old = path.read_text(encoding='utf-8')
        if '### S8.22.10.7 — Provisional game-ID crosswalk' not in old:
            path.write_text(old.rstrip() + '\n' + NOTE, encoding='utf-8')
            print('UPDATED:', path)
        else:
            print('CHECKED:', path)


if __name__ == '__main__':
    main()
