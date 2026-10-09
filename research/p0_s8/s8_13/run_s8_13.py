"""Offline S8.13 architecture self-check. Never fits a model."""
from __future__ import annotations
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import sys

import pandas as pd

from boundary import (REQUIRED_GATES, BoundaryDenied, inspect_evidence,
                      require_training_authorization, validate_research_inputs)


def load_contract(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f'S8.10 contract missing: {path}')
    spec = importlib.util.spec_from_file_location('s810_contract', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', type=Path, default=Path('.'))
    args = parser.parse_args()
    root = args.project_root.resolve()
    contract = load_contract(root / 'research/p0_s8/s8_10/contract.py')
    frame = pd.DataFrame({'minutes_last3_avg': [22.0, 24.0],
                          'target_minutes': [30, 18], 'pts': [10, 20]})
    cases = []
    def record(name, ok, detail=''):
        cases.append({'case': name, 'status': 'PASS' if ok else 'FAIL', 'detail': detail})
    good = validate_research_inputs(frame, ['minutes_last3_avg'],
                                    ['2026-01-01'], ['2026-01-02'], contract)
    record('synthetic_valid_still_blocked', good['status'] == 'SYNTHETIC_CONTRACT_PASS'
           and good['training_eligible'] is False)
    for name in ('target_minutes', 'pts'):
        bad = validate_research_inputs(frame, [name], ['2026-01-01'], ['2026-01-02'], contract)
        record(f'reject_{name}', bad['status'] == 'REJECTED_INPUT')
    overlap = validate_research_inputs(frame, ['minutes_last3_avg'],
                                       ['2026-01-02'], ['2026-01-02'], contract)
    record('reject_same_day_fold', overlap['status'] == 'REJECTED_INPUT')
    for name, evidence in [('empty_evidence', {}),
                           ('claimed_complete', {k: {'status': 'VERIFIED', 'artifact': 'self-claim'}
                                                 for k in REQUIRED_GATES})]:
        decision = inspect_evidence(evidence)
        record(name + '_blocked', decision.training_eligible is False
               and decision.decision == 'BLOCK_TRAINING')
    try:
        require_training_authorization(evidence={k: {'status': 'VERIFIED', 'artifact': 'x'}
                                                 for k in REQUIRED_GATES})
    except BoundaryDenied:
        record('authorization_unconditionally_denied', True)
    else:
        record('authorization_unconditionally_denied', False)
    result = {'milestone': 'S8.13', 'mode': 'OFFLINE_BOUNDARY_ARCHITECTURE_SELF_CHECK',
              'status': 'RESEARCH_ONLY', 'decision': 'BLOCK_TRAINING',
              'training_eligible': False, 'outcome': 'BOUNDARY_DESIGNED_NOT_INTEGRATED',
              'counts': {s: sum(c['status'] == s for c in cases) for s in ('PASS', 'FAIL')},
              'evidence_gates': inspect_evidence({}).as_dict()['gate_results'],
              'limitations': [
                  'No training entrypoint integration or runtime interception',
                  'Evidence references are not verified against independent sources',
                  'Synthetic contract checks do not certify pregame availability',
                  'No fold-local preprocessing or calibration executed',
                  'Pregame player population, DNPs, publication timestamps and 88 restart games unresolved']}
    out = root / 'research/p0_s8/s8_13/results'
    out.mkdir(parents=True, exist_ok=True)
    (out / 's8_13_report.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    with (out / 's8_13_cases.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['case', 'status', 'detail'])
        writer.writeheader()
        writer.writerows(cases)
    print(json.dumps({'milestone': 'S8.13', 'counts': result['counts'],
                      'decision': result['decision'], 'outputs': str(out)}, indent=2))
    return int(result['counts']['FAIL'] != 0)

if __name__ == '__main__':
    raise SystemExit(main())
