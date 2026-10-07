from pathlib import Path
import subprocess,sys
ROOT=Path.cwd()
def main():
    required=[
      ROOT/"src/nba_mike/features/opportunity.py",
      ROOT/"tests/test_opportunity_features.py",
      ROOT/"docs/MINUTES_ROLE_OPPORTUNITY_RESEARCH_STANDARD.md",
      ROOT/"research/p0_s4/s4/run_s4_opportunity_research.py",
    ]
    checks={"required_artifacts":all(p.exists() for p in required)}
    p=subprocess.run([sys.executable,"-m","pytest","tests/test_opportunity_features.py","-q"])
    checks["opportunity_tests"]=p.returncode==0
    doc=required[2].read_text(encoding="utf-8") if required[2].exists() else ""
    checks["d1_prior_only"]="shifted" in doc.lower() and "D-1" in doc
    checks["cold_start_explicit"]="cold-start" in doc.lower()
    checks["no_model_overclaim"]="not a production model" in doc.lower()
    print("P0-S4 S4 — Minutes / Role / Opportunity Research Acceptance")
    for k,v in checks.items(): print(f"  {k}: {'PASS' if v else 'FAIL'}")
    ok=all(checks.values());print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
