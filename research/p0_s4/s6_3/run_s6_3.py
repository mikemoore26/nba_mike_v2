"""Offline S6.3 diagnostic runner; consumes S6.2 CSV outputs, no network."""
import json
from pathlib import Path
import pandas as pd
from nba_mike.evaluation.s6_3_diagnostics import diagnostic_report

HERE=Path(__file__).resolve().parent
SEASONS=('2019-20','2023-24','2025-26')

def main():
    out=HERE/'results';out.mkdir(parents=True,exist_ok=True)
    report={'status':'RESEARCH_ONLY','seasons':{},'limitations':[
        'Historical 2025-26 season already inspected; no untouched holdout',
        'Bootstrap calendar-date intervals quantify sampling variation, not guaranteed future coverage',
        'S6.2 prediction CSVs are inputs; this stage does not train or modify a model',
        'DNPs, injury news, lineup confirmation and sportsbook markets not included',
        'No betting or production promotion']}
    for season in SEASONS:
        source=HERE.parent/'s6_2'/'results'/f's6_2_predictions_{season}.csv'
        if not source.exists():raise SystemExit(f'Missing {source}. Run S6.2 first.')
        x=pd.read_csv(source,dtype={'player_id':str,'game_id':str})
        report['seasons'][season]=diagnostic_report(x)
        m=report['seasons'][season]
        print(season,'paired games=',m['player_games'],'dates=',m['dates'],'flagged subgroups=',len(m['guardrails']))
        for candidate,comp in m['paired_comparisons'].items():
            print(' ',candidate,'coverage delta=',round(comp['coverage_delta'],4),'width delta=',round(comp['width_delta_minutes'],3))
    path=out/'s6_3_report.json';path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('S6.3 RESEARCH COMPLETE — NO PROMOTION')
if __name__=='__main__':main()
