"""Append idempotent, honest readiness audit note after a successful local run."""
import argparse
import json
from pathlib import Path

MARK = 'S8.22.10.26 OPENING-WEEK READINESS AUDIT'

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--project-root', default='.')
    a = p.parse_args()
    root = Path(a.project_root).resolve()
    report_path = root / 'research/p0_s8/s8_22_10_26/results/opening_week_readiness.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if report.get('milestone') != 'S8.22.10.26' or report.get('readiness', {}).get('real_money_approval') != 'DENIED' or report.get('training_decision') != 'BLOCK_TRAINING':
        p.exit(2, 'FAIL CLOSED: unexpected readiness report\n')
    line = f'\n## {MARK}\nRead-only static inventory: {report["inventory_file_count"]} candidate files. All operational gates NOT_VERIFIED; real-money approval DENIED. Research only; training blocked. Report: research/p0_s8/s8_22_10_26/results/opening_week_readiness.json. Next: inspect candidate files, run current-season data and OOS/odds/paper-ticket checks.\n'
    for rel in ('docs/DEVELOPMENT_JOURNAL.md', 'docs/NEXT_AGENT_HANDOFF.md'):
        path = root / rel
        if not path.is_file():
            p.exit(2, 'FAIL CLOSED: missing ' + rel + '\n')
        old = path.read_text(encoding='utf-8')
        if MARK not in old:
            path.write_text(old.rstrip() + '\n' + line, encoding='utf-8')
            print('UPDATED:', path)
        else:
            print('ALREADY RECORDED:', path)

if __name__ == '__main__':
    main()
