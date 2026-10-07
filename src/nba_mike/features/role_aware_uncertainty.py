"""Sequential role-aware residual interval calibration. Research-only."""
import math
import numpy as np
import pandas as pd

METHODS = ('pooled', 'role_specific', 'shrinkage')

def _quantile(scores, alpha):
    a = np.sort(np.asarray(scores, dtype=float))
    if len(a) == 0:
        raise ValueError('empty calibration scores')
    k = min(len(a), math.ceil((len(a) + 1) * (1 - alpha)))
    return float(a[k - 1])

def evaluate_role_calibration(frame, *, alpha=0.1, warmup_dates=30,
                              min_pooled=100, min_group=100, shrink_strength=250):
    """Predict intervals using *only earlier dates*; never use today's outcomes.

    The input should contain D-1 EWM forecasts and observed outcomes; it can
    be the saved S6 predictions. Residuals for each date are added AFTER all
    interval predictions for that date are generated.
    """
    if not 0 < alpha < 1:
        raise ValueError('alpha must be between 0 and 1')
    if min_pooled < 1 or min_group < 1 or shrink_strength < 0 or warmup_dates < 0:
        raise ValueError('invalid calibration configuration')
    required = {'event_date', 'player_id', 'game_id', 'actual', 'estimate', 'role_change_flag'}
    if required - set(frame):
        raise ValueError(f'missing columns: {sorted(required - set(frame))}')
    x = frame.copy()
    x['event_date'] = pd.to_datetime(x.event_date, errors='coerce').dt.normalize()
    if x.event_date.isna().any() or x.duplicated(['player_id', 'game_id']).any():
        raise ValueError('invalid date or duplicate player-game')
    for c in ('actual', 'estimate'):
        x[c] = pd.to_numeric(x[c], errors='coerce')
        if not np.isfinite(x[c]).all() or ((x[c] < 0) | (x[c] > 60)).any():
            raise ValueError(f'invalid {c}')
    if not x.role_change_flag.isin([0, 1]).all():
        raise ValueError('role_change_flag must be 0 or 1')
    x = x.sort_values(['event_date', 'player_id', 'game_id'], kind='stable')
    history = {0: [], 1: []}
    output = []
    for index, (date, today) in enumerate(x.groupby('event_date', sort=True)):
        all_scores = history[0] + history[1]
        if index >= warmup_dates and len(all_scores) >= min_pooled:
            pooled = _quantile(all_scores, alpha)
            radii = {}
            for group in (0, 1):
                n = len(history[group])
                group_q = _quantile(history[group], alpha) if n >= min_group else None
                # Insufficient subgroup history -> pooled fallback.
                separate = pooled if group_q is None else group_q
                weight = 0. if group_q is None else n / (n + shrink_strength) if shrink_strength else 1.
                radii[group] = (pooled, separate, (1 - weight) * pooled + weight * separate, n)
            for r in today.itertuples(index=False):
                g = int(r.role_change_flag)
                pooled_r, group_r, shrink_r, n_group = radii[g]
                for method, radius in zip(METHODS, (pooled_r, group_r, shrink_r)):
                    lo, hi = max(0., float(r.estimate) - radius), min(60., float(r.estimate) + radius)
                    output.append({'event_date': date, 'player_id': r.player_id, 'game_id': r.game_id,
                        'role_change_flag': g, 'method': method, 'actual': float(r.actual),
                        'estimate': float(r.estimate), 'lower': lo, 'upper': hi,
                        'radius': radius, 'covered': int(lo <= r.actual <= hi),
                        'abs_error': abs(float(r.actual) - float(r.estimate)),
                        'pooled_calibration_n': len(all_scores), 'group_calibration_n': n_group})
        for r in today.itertuples(index=False):
            history[int(r.role_change_flag)].append(abs(float(r.actual) - float(r.estimate)))
    return pd.DataFrame(output, columns=['event_date', 'player_id', 'game_id', 'role_change_flag',
        'method', 'actual', 'estimate', 'lower', 'upper', 'radius', 'covered', 'abs_error',
        'pooled_calibration_n', 'group_calibration_n'])

def summary(x):
    if x.empty:
        return {'n': 0, 'coverage': None, 'mean_width': None, 'mae': None,
                'error_over_5': None, 'error_over_10': None, 'error_over_15': None}
    return {'n': int(len(x)), 'coverage': float(x.covered.mean()),
            'mean_width': float((x.upper - x.lower).mean()),
            'mae': float(x.abs_error.mean()),
            'error_over_5': float((x.abs_error > 5).mean()),
            'error_over_10': float((x.abs_error > 10).mean()),
            'error_over_15': float((x.abs_error > 15).mean())}
