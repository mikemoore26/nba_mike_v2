"""S6.3 retrospective, paired, date-block diagnostics. No model promotion."""
import numpy as np
import pandas as pd

METHODS=('role_specific','role_history','role_history_volatility')
KEYS=['event_date','player_id','game_id']

def validate(frame):
    required=set(KEYS+['method','actual','estimate','lower','upper','covered','abs_error','role_change_flag','history_group','volatility_group'])
    missing=required-set(frame.columns)
    if missing: raise ValueError(f'Missing columns: {sorted(missing)}')
    x=frame.copy()
    x['event_date']=pd.to_datetime(x['event_date'],errors='coerce').dt.normalize()
    if x['event_date'].isna().any(): raise ValueError('Invalid date')
    if x.duplicated(KEYS+['method']).any():raise ValueError('Duplicate method/player-game')
    if set(x.method)!=set(METHODS):raise ValueError('Unexpected/missing methods')
    for col in ['actual','estimate','lower','upper','covered','abs_error']:
        x[col]=pd.to_numeric(x[col],errors='coerce')
        if not np.isfinite(x[col]).all():raise ValueError(f'Invalid {col}')
    if ((x['lower']>x['upper'])|(x['actual']<0)|(x['actual']>60)|(x['estimate']<0)|(x['estimate']>60)).any():
        raise ValueError('Invalid bounds or minutes')
    if not x.covered.isin([0,1]).all() or not x.role_change_flag.isin([0,1]).all():raise ValueError('Invalid binary fields')
    if not np.allclose(x.abs_error,abs(x.actual-x.estimate),atol=1e-7):raise ValueError('Inconsistent abs_error')
    if not np.array_equal(x.covered.to_numpy(),((x.actual>=x.lower)&(x.actual<=x.upper)).astype(int).to_numpy()):
        raise ValueError('Inconsistent coverage')
    counts=x.groupby(KEYS,dropna=False).method.nunique()
    if not counts.eq(len(METHODS)).all():raise ValueError('Unpaired method rows')
    baseline=x[x.method==METHODS[0]][KEYS+['actual','estimate','role_change_flag','history_group','volatility_group']]
    for method in METHODS[1:]:
        other=x[x.method==method][KEYS+['actual','estimate','role_change_flag','history_group','volatility_group']]
        matched=baseline.merge(other,on=KEYS,validate='one_to_one',suffixes=('_base','_other'))
        if len(matched)!=len(baseline):raise ValueError('Missing paired rows')
        for c in ['actual','estimate','role_change_flag','history_group','volatility_group']:
            if not matched[f'{c}_base'].equals(matched[f'{c}_other']):raise ValueError(f'Inconsistent {c} across methods')
    return x

def metrics(frame):
    if len(frame)==0:return {'n':0,'dates':0,'coverage':None,'mean_width':None,'mae':None,'error_gt_10':None,'error_gt_15':None}
    return {'n':int(len(frame)),'dates':int(frame.event_date.nunique()),'coverage':float(frame.covered.mean()),
            'mean_width':float((frame.upper-frame.lower).mean()),'mae':float(frame.abs_error.mean()),
            'error_gt_10':float((frame.abs_error>10).mean()),'error_gt_15':float((frame.abs_error>15).mean())}

def diagnostic_report(frame, *, min_group_n=100, bootstrap_reps=500, seed=63):
    """Paired bootstrap resamples calendar dates, preserving all players on each date."""
    if min_group_n<1 or bootstrap_reps<20:raise ValueError('Invalid diagnostic settings')
    x=validate(frame)
    x['month']=x.event_date.dt.strftime('%Y-%m')
    first=x.event_date.min();last=x.event_date.max()
    span=max((last-first).days,1)
    x['season_phase']=pd.cut((x.event_date-first).dt.days/span,bins=[-1e-9,1/3,2/3,1+1e-9],labels=['early','middle','late'],include_lowest=True)
    result={'status':'RESEARCH_ONLY','player_games':int(len(x)//len(METHODS)),'dates':int(x.event_date.nunique()),
            'methods':{},'paired_comparisons':{},'risk_concentrations':{},'guardrails':[]}
    for method in METHODS:
        d=x[x.method==method]
        result['methods'][method]={'overall':metrics(d),'role':{},'history':{},'volatility':{},'month':{},'phase':{}}
        for name,col in [('role','role_change_flag'),('history','history_group'),('volatility','volatility_group'),('month','month'),('phase','season_phase')]:
            for group,part in d.groupby(col,observed=True,dropna=False):
                result['methods'][method][name][str(group)]=metrics(part)
    # Error attribution only once per player-game; forecast errors do not depend on interval method.
    b=x[x.method==METHODS[0]]
    for name,col in [('role','role_change_flag'),('history','history_group'),('volatility','volatility_group')]:
        result['risk_concentrations'][name]={str(g):{'n':int(len(p)),'error_gt_10':float((p.abs_error>10).mean()),
            'error_gt_15':float((p.abs_error>15).mean()),'mae':float(p.abs_error.mean())} for g,p in b.groupby(col,dropna=False)}
    # Date-level bootstrap with paired method deltas and equal game-date resampling.
    dates=sorted(x.event_date.unique())
    rng=np.random.default_rng(seed)
    for candidate in METHODS[1:]:
        a=x[x.method==METHODS[0]][KEYS+['covered','lower','upper']]
        c=x[x.method==candidate][KEYS+['covered','lower','upper']]
        paired=a.merge(c,on=KEYS,validate='one_to_one',suffixes=('_base','_candidate'))
        paired['coverage_delta']=paired.covered_candidate-paired.covered_base
        paired['width_delta']=(paired.upper_candidate-paired.lower_candidate)-(paired.upper_base-paired.lower_base)
        per=paired.groupby('event_date').agg(n=('coverage_delta','size'),cov_sum=('coverage_delta','sum'),width_sum=('width_delta','sum')).reindex(dates)
        n=per.n.to_numpy(); cov=per.cov_sum.to_numpy();width=per.width_sum.to_numpy()
        draws=rng.integers(0,len(dates),size=(bootstrap_reps,len(dates)))
        denom=n[draws].sum(axis=1)
        cov_draw=cov[draws].sum(axis=1)/denom
        width_draw=width[draws].sum(axis=1)/denom
        result['paired_comparisons'][candidate]={'vs':'role_specific',
            'coverage_delta':float(cov.sum()/n.sum()),'coverage_delta_date_bootstrap_95ci':[float(z) for z in np.quantile(cov_draw,[.025,.975])],
            'width_delta_minutes':float(width.sum()/n.sum()),'width_delta_date_bootstrap_95ci':[float(z) for z in np.quantile(width_draw,[.025,.975])],
            'bootstrap_reps':bootstrap_reps,'bootstrap_unit':'calendar_date'}
    # Flag concerning subgroups without implying statistical proof.
    for method in METHODS:
        for dimension in ['role','history','volatility','phase']:
            for group,m in result['methods'][method][dimension].items():
                if m['n']>=min_group_n and m['coverage']<.88:
                    result['guardrails'].append({'method':method,'dimension':dimension,'group':group,'n':m['n'],
                        'coverage':m['coverage'],'issue':'coverage_below_88_percent'})
    return result
