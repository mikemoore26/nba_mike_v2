"""S6.2 offline conditional interval study; comparisons restricted to common rows."""
import json
from pathlib import Path
import pandas as pd
from nba_mike.features.conditional_uncertainty import evaluate_conditional, summary, METHODS

HERE=Path(__file__).resolve().parent
SEASONS=('2019-20','2023-24','2025-26')

def main():
    out=HERE/'results';out.mkdir(parents=True,exist_ok=True)
    report={'status':'RESEARCH_ONLY','methods':list(METHODS)+['s6_1_pooled','s6_1_shrinkage'],
        'seasons':{},'limitations':['2025-26 already inspected: no pristine holdout',
        'Volatility proxy uses only prior player prediction errors, not raw minutes variance',
        'Fixed five-minute volatility threshold and min-cell fallback require future validation',
        'All methods evaluated on identical S6.1 eligible player-games',
        'Marginal calibration does not ensure player-level coverage',
        'No injury, DNP, confirmed lineup, odds or betting validation']}
    for season in SEASONS:
        base=HERE.parent/'s6'/'results'/f's6_predictions_{season}.csv'
        previous=HERE.parent/'s6_1'/'results'/f's6_1_predictions_{season}.csv'
        if not base.exists() or not previous.exists():
            raise SystemExit('Missing S6/S6.1 predictions. Run those research steps first.')
        x=pd.read_csv(base,dtype={'player_id':str,'game_id':str})
        prior=pd.read_csv(previous,dtype={'player_id':str,'game_id':str})
        current=evaluate_conditional(x)
        # Align to the EXACT S6.1 player-games, without duplicating rows across methods.
        keys=['event_date','player_id','game_id']
        current['event_date']=pd.to_datetime(current.event_date).dt.strftime('%Y-%m-%d')
        prior['event_date']=pd.to_datetime(prior.event_date).dt.strftime('%Y-%m-%d')
        common=prior[keys].drop_duplicates()
        current=current.merge(common,on=keys,how='inner',validate='many_to_one')
        prior=prior.merge(current[keys].drop_duplicates(),on=keys,how='inner',validate='many_to_one')
        n=current[keys].drop_duplicates().shape[0]
        if n==0:raise SystemExit('No common rows')
        if n!=prior[keys].drop_duplicates().shape[0]:raise SystemExit('Paired sample mismatch')
        report['seasons'][season]={'common_player_games':int(n),'methods':{}}
        for method in METHODS:
            d=current[current.method==method]
            report['seasons'][season]['methods'][method]={
                'overall':summary(d),'stable':summary(d[d.role_change_flag==0]),
                'role_change':summary(d[d.role_change_flag==1]),
                'history':{g:summary(t) for g,t in d.groupby('history_group')},
                'volatility':{g:summary(t) for g,t in d.groupby('volatility_group')}}
        for old,new in [('pooled','s6_1_pooled'),('shrinkage','s6_1_shrinkage')]:
            d=prior[prior.method==old]
            report['seasons'][season]['methods'][new]={
                'overall':summary(d),'stable':summary(d[d.role_change_flag==0]),
                'role_change':summary(d[d.role_change_flag==1])}
        current.to_csv(out/f's6_2_predictions_{season}.csv',index=False)
        print(season,'paired n=',n,'role-change coverage=',{
            m:round(v['role_change']['coverage'],4) for m,v in report['seasons'][season]['methods'].items()})
    (out/'s6_2_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('S6.2 RESEARCH COMPLETE — NO PROMOTION')
if __name__=='__main__':main()
