"""S8.8: offline adversarial behavioral checks against the real S4/S5 builders.
No model training, no network, no production writes. Fail closed on missing imports.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

REALIZED_STATS=('min','pts','reb','ast','fg3m')
FIELDS = ('game_id','event_date','player_id','team_id','min','pts','reb','ast','fg3m')

def sample():
    rows=[]
    for player,offset in [('A',0),('B',6)]:
        for i in range(12):
            rows.append(dict(game_id=f'{player}{i}',event_date=f'2025-01-{i+1:02d}',player_id=player,
                team_id=f'T{player}',min=float(18+offset+i),pts=float(8+offset+i),
                reb=float(2+i%5),ast=float(1+i%4),fg3m=float(i%3)))
    # two games for A on Jan 6; same-day outcomes must not affect each other
    rows.append(dict(game_id='A5b',event_date='2025-01-06',player_id='A',team_id='TA',
        min=40.,pts=31.,reb=7.,ast=6.,fg3m=4.))
    return pd.DataFrame(rows,columns=FIELDS)

def comparable(frame):
    return frame.drop(columns=['target_minutes','pts','reb','ast','fg3m'],errors='ignore').sort_values(['player_id','game_id']).reset_index(drop=True).sort_index(axis=1)

def before(frame,day):
    return frame.loc[pd.to_datetime(frame.event_date)<pd.Timestamp(day)]

def on(frame,day):
    return frame.loc[pd.to_datetime(frame.event_date)==pd.Timestamp(day)]

def same(a,b):
    assert_frame_equal(comparable(a),comparable(b),check_dtype=False,check_like=True)

def run_cases(name,builder):
    x=sample(); original=builder(x.copy()); checks=[]
    def check(case,fn):
        try: fn();checks.append(dict(builder=name,case=case,status='PASS',detail=''))
        except Exception as exc: checks.append(dict(builder=name,case=case,status='FAIL',detail=f'{type(exc).__name__}: {str(exc)[:300]}'))
    def mutation_target():
        z=x.copy();z.loc[z.game_id=='A5','min']=55;z.loc[z.game_id=='A5',['pts','reb','ast','fg3m']]=[55,15,12,9]
        changed=builder(z)
        same(on(original,'2025-01-06'),on(changed,'2025-01-06'))
        same(before(original,'2025-01-06'),before(changed,'2025-01-06'))
    check('same_day_outcome_mutation_invariance',mutation_target)
    def future_mutation():
        z=x.copy();z.loc[z.game_id=='A10','min']=59;z.loc[z.game_id=='A10','pts']=60
        same(before(original,'2025-01-11'),before(builder(z),'2025-01-11'))
    check('future_outcome_mutation_invariance',future_mutation)
    def player_isolation():
        z=x.copy();z.loc[z.player_id=='B','min']=59;z.loc[z.player_id=='B','pts']=40
        same(original.loc[original.player_id=='A'],builder(z).loc[lambda q:q.player_id=='A'])
    check('player_history_isolation',player_isolation)
    def order_invariance():
        z=x.sample(frac=1,random_state=83).reset_index(drop=True)
        same(original,builder(z))
    check('input_row_order_invariance',order_invariance)
    def target_boundary():
        if 'target_minutes' not in original.columns:raise AssertionError('missing target_minutes')
        if 'min' in original.columns:raise AssertionError('realized min remains in output')
        if original['target_minutes'].isna().any():raise AssertionError('missing target minutes')
        # Explicitly NOT a downstream feature allowlist proof.
    check('target_minutes_separated_from_realized_min',target_boundary)
    def cold_start():
        first=original.loc[original.game_id=='A0'].iloc[0]
        if int(first['prior_games'])!=0:raise AssertionError('first game has prior games')
        if name=='adaptive_form' and not pd.isna(first['last_5']):raise AssertionError('cold start last_5 non-null')
        if name=='opportunity' and not pd.isna(first['minutes_last5_avg']):raise AssertionError('cold start minutes_last5_avg non-null')
    check('cold_start_no_fabricated_history',cold_start)
    def same_day_pair():
        f=original.set_index('game_id'); a=f.loc['A5'];b=f.loc['A5b']
        excluded={'game_id','target_minutes','pts','reb','ast','fg3m'}
        # Same-date rows can differ in game_id/target, but not historical features.
        for col in f.columns:
            if col in excluded:continue
            va,vb=a[col],b[col]
            if pd.isna(va) and pd.isna(vb):continue
            if va!=vb:raise AssertionError(f'same-day mismatch: {col}')
    check('same_day_games_share_pregame_history',same_day_pair)
    return checks

def execute(root):
    sys.path.insert(0,str(root/'src'))
    try:
        from nba_mike.features.opportunity import build_opportunity_research_frame
        from nba_mike.features.adaptive_form import make_form_frame
    except Exception as exc:
        return [dict(builder='IMPORT',case='load_real_builders',status='BLOCKED',detail=f'{type(exc).__name__}: {exc}')]
    results=[]
    for name,func in [('opportunity',build_opportunity_research_frame),('adaptive_form',make_form_frame)]:
        try: results+=run_cases(name,func)
        except Exception as exc: results.append(dict(builder=name,case='builder_execution',status='FAIL',detail=f'{type(exc).__name__}: {exc}'))
    return results

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');p.add_argument('--output-dir',default=None)
    a=p.parse_args();root=Path(a.project_root).resolve()
    output=Path(a.output_dir).resolve() if a.output_dir else root/'research/p0_s8/s8_8/results'
    output.mkdir(parents=True,exist_ok=True)
    results=execute(root)
    with (output/'s8_8_cases.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['builder','case','status','detail']);w.writeheader();w.writerows(results)
    sha={}
    for path in ['src/nba_mike/features/opportunity.py','src/nba_mike/features/adaptive_form.py']:
        f=root/path;sha[path]=hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None
    counts={status:sum(r['status']==status for r in results) for status in ('PASS','FAIL','BLOCKED')}
    report=dict(milestone='S8.8',mode='OFFLINE_ADVERSARIAL_BEHAVIOR_TEST',run_utc=datetime.now(timezone.utc).isoformat(),
        status='RESEARCH_ONLY',decision='BLOCK_TRAINING',training_eligible=False,counts=counts,
        outcome='BEHAVIOR_TESTS_PASS_NOT_ASOF_CERTIFIED' if counts['PASS']==14 and not counts['FAIL'] and not counts['BLOCKED'] else 'REQUIRES_REVIEW',
        source_sha256=sha,cases=results,unresolved_gates=[
        'Historical pre-tipoff publication and snapshot timestamps unverified',
        'Pregame player universe and DNP reconciliation unavailable',
        'Target excluded from downstream training matrix not established',
        'Adaptive form retains realized box-score columns if supplied; downstream must explicitly exclude them',
        'Fold-local training preprocessing/calibration not verified',
        '88 historical restart calendar games unverified',
        'Synthetic tests do not prove all real-world join and pipeline behavior'])
    (output/'s8_8_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'outcome':report['outcome'],'counts':counts,'output':str(output)},indent=2))
    return 0 if report['outcome']=='BEHAVIOR_TESTS_PASS_NOT_ASOF_CERTIFIED' else 2
if __name__=='__main__':raise SystemExit(main())
