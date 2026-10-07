"""Historical S5 research: reuses S4's season fetcher; never modifies S4 reports."""
import json
import sys
from pathlib import Path
import pandas as pd
from nba_mike.features.adaptive_form import make_form_frame,score_forecasts,expanding_prequential

ROOT=Path(__file__).resolve().parents[1]/"s4"
sys.path.insert(0,str(ROOT))
from run_s4_opportunity_research import fetch, SEASONS  # noqa: E402

OUT=Path(__file__).resolve().parent/"results"

def mae(x,y):return float((x-y).abs().mean()) if len(x) else None

def main():
    OUT.mkdir(exist_ok=True,parents=True)
    report={"status":"RESEARCH_ONLY", "seasons":{},"method":"D-1 date-safe candidate features, prequential pooled global selector, last-5 comparator"}
    records=[]
    for season in SEASONS:
        frame=make_form_frame(fetch(season))
        candidate=score_forecasts(frame)
        preq=expanding_prequential(frame)
        row={"source_rows":len(frame),"evaluated_rows":len(preq),
             "last5_mae":mae(preq.baseline,preq.actual),
             "adaptive_mae":mae(preq.adaptive,preq.actual),
             "candidate_scores":candidate.to_dict(orient="records"),
             "selected_counts":preq.selected.value_counts().to_dict(),
             "role_segments":{}}
        for label,part in (("stable",preq.loc[preq.role_change_flag==0]),
                           ("role_change",preq.loc[preq.role_change_flag==1])):
            row["role_segments"][label]={"n":len(part),"last5_mae":mae(part.baseline,part.actual),"adaptive_mae":mae(part.adaptive,part.actual)}
        report["seasons"][season]=row
        records.extend([{"season":season,**r} for r in candidate.to_dict(orient="records")])
        print(f"{season}: n={len(preq)} last5={row['last5_mae']} adaptive={row['adaptive_mae']}")
    report["limitations"]=[
        "This is a research-only expanding prequential evaluation, not a locked final holdout",
        "The selector is global and uses prior observed errors, not individualized player selection",
        "S4 and S5 windows count prior distinct calendar dates; multiple same-day games are averaged",
        "The prequential warmup and 100-error minimum are research design choices",
        "Historical data fetched live; source snapshot/manifest is not yet immutable",
        "Injuries, confirmed lineups, DNPs and market odds are not incorporated",
        "No betting or model-training promotion is authorized",
    ]
    (OUT/"s5_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    pd.DataFrame(records).to_csv(OUT/"s5_candidates.csv",index=False)
    print("S5 RESEARCH COMPLETE")

if __name__=="__main__":main()
