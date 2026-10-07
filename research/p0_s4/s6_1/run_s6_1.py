"""Offline S6.1 study on frozen S6 predictions. No API calls."""
import argparse
import json
from pathlib import Path
import pandas as pd
from nba_mike.features.role_aware_uncertainty import evaluate_role_calibration, summary, METHODS

HERE = Path(__file__).resolve().parent
S6_RESULTS = HERE.parent / 's6' / 'results'
SEASONS = ('2019-20', '2023-24', '2025-26')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--alpha', type=float, default=.1)
    args = parser.parse_args()
    report = {'status': 'RESEARCH_ONLY', 'alpha': args.alpha,
        'methods': list(METHODS), 'seasons': {},
        'cautions': ['S6 outputs are retrospective and 2025-26 was previously inspected',
            'All methods use only prior-date residuals; calibration is reset per season',
            'Marginal empirical coverage is not a guarantee of subgroup coverage',
            'No DNP, injury, confirmed lineup, or market data',
            'This is a research comparison, not production or betting validation']}
    out = HERE / 'results'
    out.mkdir(parents=True, exist_ok=True)
    for season in SEASONS:
        path = S6_RESULTS / f's6_predictions_{season}.csv'
        if not path.exists():
            raise SystemExit(f'Missing {path}. Run S6 first.')
        data = pd.read_csv(path, dtype={'player_id': str, 'game_id': str})
        scored = evaluate_role_calibration(data, alpha=args.alpha)
        scored.to_csv(out / f's6_1_predictions_{season}.csv', index=False)
        report['seasons'][season] = {}
        for method in METHODS:
            part = scored[scored.method == method]
            report['seasons'][season][method] = {
                'overall': summary(part),
                'stable': summary(part[part.role_change_flag == 0]),
                'role_change': summary(part[part.role_change_flag == 1])}
        print(season, {m: report['seasons'][season][m]['role_change']['coverage'] for m in METHODS})
    (out / 's6_1_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('S6.1 RESEARCH COMPLETE — no promotion')
if __name__ == '__main__':
    main()
