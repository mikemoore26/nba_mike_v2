"""Append-only, idempotent milestone note to existing journal and handoff.

Never creates an absent journal: a missing journal needs manual investigation.
"""
from pathlib import Path
import argparse

MARKER = '<!-- NBA_MIKE_S8_22_10_31 -->'
JOURNAL = '''\n\n{marker}\n## S8.22.10.31 — Canonical-to-D-1 adapter\n- Previous S8.22.10.30: 7 synthetic cross-module tests passed on user Windows environment; Git commit `5aa18df` pushed to `main`.\n- New: explicit, fail-closed canonical-to-snapshot adapter; validates artifact hash/path/row count, exact schema, numeric ranges, duplicate keys, D-1 boundaries and metadata.\n- Local isolated tests against uploaded module source: 12 passed; repository test outcome must be recorded separately.\n- Decision: RESEARCH_ONLY / BLOCK_TRAINING / REAL-MONEY DENIED. Historical publication/as-of evidence is not certified.\n- Follow-up: verify repository tests and establish as-of provenance gates before any model training.\n'''.format(marker=MARKER)
HANDOFF = '''\n\n{marker}\n## Latest milestone — S8.22.10.31\nS8.22.10.30 completed: 7/7 synthetic integration tests passed on user Windows, commit `5aa18df` pushed. S8.22.10.31 adds `src/nba_mike/adapters/canonical_snapshot.py`, strict canonical-to-D-1 mapping and `tests/test_s8221031_adapter.py` (12 isolated local passes; run in actual repo). See `docs/S8_22_10_31_ADAPTER_CONTRACT.md`. Do not assume historical as-of availability. Current governance: RESEARCH_ONLY / BLOCK_TRAINING / REAL-MONEY DENIED. Next: inspect user test output, as-of certification, and maintain fail-closed behavior.\n'''.format(marker=MARKER)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', type=Path, default=Path('.'))
    args = parser.parse_args()
    root = args.project_root.resolve()
    targets = [(root / 'docs/DEVELOPMENT_JOURNAL.md', JOURNAL),
               (root / 'docs/NEXT_AGENT_HANDOFF.md', HANDOFF)]
    missing = [str(path) for path, _ in targets if not path.is_file()]
    if missing:
        raise SystemExit(f'ABORT: required journals missing: {missing}')
    for path, content in targets:
        old = path.read_text(encoding='utf-8')
        if MARKER in old:
            print(f'ALREADY PRESENT: {path}')
            continue
        path.write_text(old.rstrip() + content + '\n', encoding='utf-8')
        print(f'APPENDED: {path}')


if __name__ == '__main__':
    main()
