from pathlib import Path
import pandas as pd
from nba_mike.features import validate_feature_registry

ROOT=Path.cwd()
REG=ROOT/"config/p0_s4_baseline_feature_registry.csv"
DOC=ROOT/"docs/FEATURE_REGISTRY_STANDARD.md"

def main():
    checks={"required_artifacts":REG.exists() and DOC.exists()}
    df=pd.read_csv(REG)
    for c in ["pregame_available","historical_available","today_available","leakage_checked"]:
        df[c]=df[c].map({"true":True,"false":False,True:True,False:False})
    checked=validate_feature_registry(df)
    checks["registry_valid"]=len(checked)==len(df)
    checks["approved_baselines_present"]=(checked.research_status=="APPROVED_BASELINE").sum()>=10
    checks["research_only_present"]=(checked.research_status=="RESEARCH_ONLY").any()
    checks["intraday_blocked"]=set(checked.loc[checked.feature_group=="intraday","research_status"])=={"BLOCKED"}
    checks["market_blocked"]=set(checked.loc[checked.feature_group=="market","research_status"])=={"BLOCKED"}
    checks["d1_documented"]="D-1" in DOC.read_text(encoding="utf-8")
    print("P0-S4 S3 — Baseline Feature Registry")
    for k,v in checks.items(): print(f"  {k}: {'PASS' if v else 'FAIL'}")
    ok=all(checks.values()); print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
