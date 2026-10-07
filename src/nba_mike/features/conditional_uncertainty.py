"""Chronological conditional residual calibration; research-only.

All forecasts on a calendar date share calibration built before that date.
"""
import math
from collections import defaultdict

import numpy as np
import pandas as pd

METHODS = ('role_specific', 'role_history', 'role_history_volatility')


def _q(values, alpha):
    values = np.sort(np.asarray(values, dtype=float))
    k = min(len(values), math.ceil((len(values) + 1) * (1 - alpha)))
    return float(values[k - 1])


def _depth(n):
    return '5-9' if n < 10 else '10-19' if n < 20 else '20+'


def evaluate_conditional(frame, *, alpha=.1, warmup_dates=30, min_pooled=100,
                         min_group=100, min_cell=100, recent_errors=8):
    """Evaluate intervals using strictly prior-date errors, with sparse-cell fallback.

    Volatility tier is based on the *previous* recent_errors absolute forecast errors
    of the same player, and requires >=3 past residuals. Threshold is fixed at 5 min.
    This is a preregistered exploratory heuristic, not a tuned optimum.
    """
    if not 0 < alpha < 1 or min_pooled < 1 or min_group < 1 or min_cell < 1 or recent_errors < 3 or warmup_dates < 0:
        raise ValueError('invalid configuration')
    required = {'event_date','player_id','game_id','actual','estimate','role_change_flag','prior_dates'}
    if required - set(frame):
        raise ValueError(f'missing: {sorted(required-set(frame))}')
    x = frame.copy()
    x['event_date'] = pd.to_datetime(x.event_date, errors='coerce').dt.normalize()
    if x.event_date.isna().any() or x.duplicated(['player_id','game_id']).any():
        raise ValueError('invalid date or duplicate player-game')
    for c in ('actual','estimate','prior_dates'):
        x[c] = pd.to_numeric(x[c],errors='coerce')
        if not np.isfinite(x[c]).all(): raise ValueError(f'invalid {c}')
    if ((x.actual<0)|(x.actual>60)|(x.estimate<0)|(x.estimate>60)|(x.prior_dates<0)).any():
        raise ValueError('invalid minutes or history')
    if not x.role_change_flag.isin([0,1]).all():raise ValueError('invalid role flag')
    x=x.sort_values(['event_date','player_id','game_id'],kind='stable')
    pooled=[]; roles=defaultdict(list); depths=defaultdict(list); cells=defaultdict(list)
    player_history=defaultdict(list)
    output=[]
    for date_index,(date,today) in enumerate(x.groupby('event_date',sort=True)):
        staged=[]
        for r in today.itertuples(index=False):
            role=int(r.role_change_flag); depth=_depth(int(r.prior_dates))
            previous=player_history[str(r.player_id)]
            vol='unknown' if len(previous)<3 else ('high' if float(np.mean(previous[-recent_errors:]))>5 else 'low')
            staged.append((r,role,depth,vol))
        if date_index>=warmup_dates and len(pooled)>=min_pooled:
            pq=_q(pooled,alpha)
            for r,role,depth,vol in staged:
                role_hist=roles[role]; depth_hist=depths[(role,depth)]; cell_hist=cells[(role,depth,vol)]
                rq=_q(role_hist,alpha) if len(role_hist)>=min_group else pq
                dq=_q(depth_hist,alpha) if len(depth_hist)>=min_cell else rq
                cq=_q(cell_hist,alpha) if len(cell_hist)>=min_cell else dq
                for method,radius in zip(METHODS,(rq,dq,cq)):
                    low=max(0.,float(r.estimate)-radius); high=min(60.,float(r.estimate)+radius)
                    actual=float(r.actual)
                    output.append({'event_date':date,'player_id':r.player_id,'game_id':r.game_id,
                        'role_change_flag':role,'history_group':depth,'volatility_group':vol,
                        'method':method,'actual':actual,'estimate':float(r.estimate),
                        'lower':low,'upper':high,'radius':radius,'covered':int(low<=actual<=high),
                        'abs_error':abs(actual-float(r.estimate)),
                        'role_calibration_n':len(role_hist),'depth_calibration_n':len(depth_hist),
                        'cell_calibration_n':len(cell_hist)})
        # Update calibration only after ALL forecasts for this date.
        for r,role,depth,vol in staged:
            error=abs(float(r.actual)-float(r.estimate))
            pooled.append(error);roles[role].append(error)
            depths[(role,depth)].append(error);cells[(role,depth,vol)].append(error)
            player_history[str(r.player_id)].append(error)
    return pd.DataFrame(output,columns=['event_date','player_id','game_id','role_change_flag',
        'history_group','volatility_group','method','actual','estimate','lower','upper','radius',
        'covered','abs_error','role_calibration_n','depth_calibration_n','cell_calibration_n'])


def summary(x):
    if x.empty:return {'n':0,'coverage':None,'mean_width':None,'mae':None}
    return {'n':int(len(x)),'coverage':float(x.covered.mean()),
            'mean_width':float((x.upper-x.lower).mean()),'mae':float(x.abs_error.mean())}
