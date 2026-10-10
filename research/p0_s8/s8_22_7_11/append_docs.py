"""Idempotently append milestone notes to existing primary docs without replacing content."""
import argparse
from pathlib import Path

MARKER = '<!-- S8.22.7.11 documentation checkpoint -->'


def append_once(root, target, fragment):
    root = Path(root).resolve()
    dst = (root / target).resolve()
    src = (root / fragment).resolve()
    if not dst.is_relative_to(root) or not src.is_relative_to(root) or not dst.is_file() or not src.is_file():
        raise ValueError('Required existing documentation or fragment missing')
    original = dst.read_text(encoding='utf-8')
    if MARKER in original:
        return 'ALREADY_PRESENT'
    addition = src.read_text(encoding='utf-8')
    if not addition.strip():
        raise ValueError('Empty fragment')
    backup = dst.with_name(dst.name + '.pre_s822711.bak')
    if backup.exists():
        raise ValueError('Backup already exists but marker absent; manual review required')
    backup.write_bytes(dst.read_bytes())
    with dst.open('a', encoding='utf-8', newline='\n') as f:
        f.write('\n\n' + MARKER + '\n' + addition.rstrip() + '\n')
    return 'APPENDED_WITH_BACKUP'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--project-root', default='.')
    a = p.parse_args()
    pairs = [
        ('docs/DEVELOPMENT_JOURNAL.md', 'docs/S8_22_7_11_JOURNAL_APPEND.md'),
        ('docs/NEXT_AGENT_HANDOFF.md', 'docs/S8_22_7_11_HANDOFF_APPEND.md'),
    ]
    for target, fragment in pairs:
        print(target, append_once(a.project_root, target, fragment))


if __name__ == '__main__':
    main()
