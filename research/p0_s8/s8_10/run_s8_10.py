"""Offline contract self-check. No model fit or source mutation."""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

try:
    from .contract import ContractViolation, assert_research_only, validate_chronological_fold, validate_predictors
except ImportError:
    from contract import ContractViolation, assert_research_only, validate_chronological_fold, validate_predictors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', default='.')
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    out = root / 'research/p0_s8/s8_10/results'
    out.mkdir(parents=True, exist_ok=True)
    cases = []

    def check(name, func, should_reject=False):
        try:
            func()
            passed = not should_reject
            detail = '' if passed else 'Expected rejection but accepted'
        except ContractViolation as exc:
            passed = should_reject
            detail = str(exc)
        except Exception as exc:
            passed = False
            detail = f'Unexpected {type(exc).__name__}: {exc}'
        cases.append({'case': name, 'status': 'PASS' if passed else 'FAIL', 'detail': detail})

    sample = pd.DataFrame({'minutes_last5_avg': [23., 25.], 'target_minutes': [29., 31.], 'pts': [11, 14]})
    check('explicit_allowlist', lambda: validate_predictors(sample, ['minutes_last5_avg']))
    check('reject_target', lambda: validate_predictors(sample, ['target_minutes']), True)
    check('reject_outcome', lambda: validate_predictors(sample, ['pts']), True)
    check('reject_empty_allowlist', lambda: validate_predictors(sample, []), True)
    check('reject_nonfinite', lambda: validate_predictors(pd.DataFrame({'feature': [float('nan')]}), ['feature']), True)
    check('ordered_fold', lambda: validate_chronological_fold(['2024-01-01'], ['2024-01-02']))
    check('reject_same_day', lambda: validate_chronological_fold(['2024-01-01'], ['2024-01-01']), True)
    check('reject_overlap', lambda: validate_chronological_fold(['2024-01-04'], ['2024-01-02']), True)
    check('training_stays_blocked', assert_research_only, True)
    src = Path(__file__).with_name('contract.py')
    report = {
        'milestone': 'S8.10', 'mode': 'STANDALONE_FAIL_CLOSED_CONTRACT_SELF_CHECK',
        'run_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'RESEARCH_ONLY', 'decision': 'BLOCK_TRAINING', 'training_eligible': False,
        'counts': {k: sum(c['status'] == k for c in cases) for k in ('PASS', 'FAIL')},
        'source_sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
        'outcome': 'CONTRACT_SELF_CHECK_ONLY_NOT_INTEGRATED',
        'limitations': [
            'Not connected to model training or prediction; no live X matrix inspected',
            'Allowed predictor names require separate as-of lineage verification',
            'No independent pregame eligibility, DNP, or historical publication timestamps',
            'No fold-local preprocessing or calibration verification',
            '88 historical restart games remain unverified',
        ],
    }
    with (out / 's8_10_cases.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['case', 'status', 'detail'])
        writer.writeheader()
        writer.writerows(cases)
    (out / 's8_10_report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['counts']['FAIL'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
