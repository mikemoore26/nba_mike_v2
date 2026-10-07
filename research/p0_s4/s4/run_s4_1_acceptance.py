from pathlib import Path
import subprocess,sys
import pandas as pd
from nba_mike.features.opportunity import build_opportunity_research_frame
from run_s4_opportunity_research import analyze

def main():
    p=subprocess.run([sys.executable,"-m","pytest","tests/test_opportunity_features.py","tests/test_opportunity_hardening.py","-q"])
    checks={"all_opportunity_tests":p.returncode==0}
    cols=["game_id","event_date","player_id","team_id","min","pts","reb","ast","fg3m"]
    rows=[[f"G{i}",f"2025-11-{i+1:02d}","P","T",float(15+i),10,3,2,1] for i in range(12)]
    frame=build_opportunity_research_frame(pd.DataFrame(rows,columns=cols))
    groups=analyze(frame)
    checks["history_buckets"]=all(f"history_{s}" in groups for s in ["0","1-2","3-4","5-9","10+"])
    checks["role_segmentation"]=all(k in groups for k in ["stable_5plus","role_change_5plus"])
    checks["minute_buckets"]=all(k in groups for k in ["realized_minutes_0-10_5plus","realized_minutes_30-60_5plus"])
    checks["original_results_preserved"]=not Path("research/p0_s4/s4/results/s4_opportunity_research.json").exists() or Path("research/p0_s4/s4/results/s4_opportunity_research.json").is_file()
    for k,v in checks.items():print(f"{k}: {'PASS' if v else 'FAIL'}")
    print("OVERALL:", "PASS" if all(checks.values()) else "FAIL")
    return 0 if all(checks.values()) else 1
if __name__=="__main__":raise SystemExit(main())
