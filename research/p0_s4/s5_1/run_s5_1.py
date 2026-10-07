"""Frozen-season holdout comparison, immutable local raw snapshot, day-block bootstrap."""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from nba_mike.features.adaptive_form import make_form_frame, CANDIDATES

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 's4'))
from run_s4_opportunity_research import fetch  # noqa: E402
SEASONS = ('2019-20','2023-24','2025-26')
COLUMNS = ('game_id','event_date','player_id','team_id','min','pts','reb','ast','fg3m')
SNAPSHOT = Path(__file__).resolve().parent / 'snapshots'
RESULTS = Path(__file__).resolve().parent / 'results'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_season(season, *, refresh=False):
    SNAPSHOT.mkdir(parents=True,exist_ok=True)
    p=SNAPSHOT / f'player_gamelogs_{season}.csv'
    if refresh or not p.exists():
        if p.exists():
            raise RuntimeError(f'Snapshot already exists: {p}. Move it manually before refreshing.')
        data=fetch(season).loc[:,COLUMNS].sort_values(['event_date','game_id','player_id'])
        data.to_csv(p,index=False)
    return pd.read_csv(p,dtype={'game_id':str,'player_id':str,'team_id':str}), {'file':p.name,'sha256':sha(p),'rows':int(len(pd.read_csv(p)))}

def paired_bootstrap(frame, left='last_5', right='ewm_5', iterations=2000, seed=517):
    """Sample game dates, preserving within-day dependence. Positive = right wins."""
    x=frame[['event_date','target_minutes',left,right]].dropna().copy()
    x['gain']=(x.target_minutes-x[left]).abs()-(x.target_minutes-x[right]).abs()
    daily=x.groupby('event_date').gain.agg(['sum','count'])
    if daily.empty: raise ValueError('no comparable outcomes')
    rng=np.random.default_rng(seed)
    vals=daily[['sum','count']].to_numpy(dtype=float)
    boot=[]
    for _ in range(iterations):
        draw=vals[rng.integers(0,len(vals),size=len(vals))]
        boot.append(draw[:,0].sum()/draw[:,1].sum())
    return {'n':len(x),'dates':len(daily),'mae_left':float((x.target_minutes-x[left]).abs().mean()),
            'mae_right':float((x.target_minutes-x[right]).abs().mean()),
            'gain_minutes':float(x.gain.mean()),'gain_ci95':list(map(float,np.quantile(boot,[.025,.975])))}

def evaluate(train, holdout):
    train=train[train.prior_dates>=5].copy()
    holdout=holdout[holdout.prior_dates>=5].copy()
    scores={c:float((train.target_minutes-train[c]).abs().mean()) for c in CANDIDATES}
    selected=min(CANDIDATES,key=lambda c:(scores[c],CANDIDATES.index(c)))
    result={'train_rows':len(train),'holdout_rows':len(holdout),'selected_from_training':selected,
            'train_candidate_mae':scores,'holdout':{
                'ewm5_vs_last5':paired_bootstrap(holdout),
                'selected_vs_last5':paired_bootstrap(holdout,right=selected),
            },'role_groups':{}}
    for label,subset in [('stable',holdout[holdout.role_change_flag==0]),('role_change',holdout[holdout.role_change_flag==1])]:
        result['role_groups'][label]=paired_bootstrap(subset) if len(subset)>0 else None
    for k in ('5-9','10-19','20+'):
        lo,hi={'5-9':(5,10),'10-19':(10,20),'20+':(20,float('inf'))}[k]
        part=holdout[(holdout.prior_dates>=lo)&(holdout.prior_dates<hi)]
        result['role_groups']['history_'+k]=paired_bootstrap(part) if len(part)>0 else None
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--offline',action='store_true',help='Require pre-existing snapshots; no downloads')
    args=parser.parse_args()
    frames={}; manifest={}
    for season in SEASONS:
        if args.offline and not (SNAPSHOT/f'player_gamelogs_{season}.csv').exists():
            raise SystemExit(f'Missing offline snapshot for {season}')
        raw,meta=load_season(season)
        manifest[season]=meta
        frames[season]=make_form_frame(raw)
    train=pd.concat([frames[s] for s in SEASONS[:2]],ignore_index=True)
    result=evaluate(train,frames[SEASONS[2]])
    result.update({'status':'RESEARCH_ONLY','training_seasons':list(SEASONS[:2]),'locked_holdout_season':SEASONS[2],
                   'snapshots':manifest,'bootstrap':'2000 seeded date-block resamples',
                   'cautions':['Season selection and EWM-5 hypothesis were informed by prior S5 research including 2025-26; this is a retrospective confirmation, NOT a genuinely untouched holdout.',
                   'Source snapshots created after original research; original historical provenance cannot be retroactively established.',
                   'No DNP, injury, lineup, or sportsbook data; not a betting edge.',
                   'Within-season features use only prior calendar dates; no cross-season feature history.',
                   'CI reflects game-date sampling, not player/season clustering or multiple comparisons.']})
    RESULTS.mkdir(parents=True,exist_ok=True)
    (RESULTS/'s5_1_report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    (RESULTS/'s5_1_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Training-selected:',result['selected_from_training'])
    print('EWM-5 holdout:',result['holdout']['ewm5_vs_last5'])
    print('S5.1 RESEARCH COMPLETE — retrospective confirmation only')

if __name__=='__main__':main()
