from pathlib import Path
import subprocess, sys

ROOT=Path.cwd()
required=[
 ROOT/"docs/TARGET_OUTCOME_CONTRACT.md",
 ROOT/"src/nba_mike/targets/__init__.py",
 ROOT/"src/nba_mike/targets/builder.py",
 ROOT/"tests/test_target_builder.py",
]
def main():
    checks={"required_artifacts": all(p.exists() for p in required)}
    doc=(ROOT/"docs/TARGET_OUTCOME_CONTRACT.md").read_text(encoding="utf-8") if required[0].exists() else ""
    checks["target_semantics"]=all(x in doc for x in ["target_minutes","target_points","target_rebounds","target_assists","target_3pm"])
    checks["dnp_not_fabricated"]="Missing minutes are not converted to zero." in doc
    checks["component_policy"]="PRA/PR/PA/RA" in doc
    checks["leakage_boundary"]="D-1" in doc and "cannot be joined into the feature side" in doc
    p=subprocess.run([sys.executable,"-m","pytest","tests/test_target_builder.py","-q"])
    checks["target_tests"]=p.returncode==0
    print("P0-S4 S2 — Target Contract & Outcome Builder")
    for k,v in checks.items(): print(f"  {k}: {'PASS' if v else 'FAIL'}")
    ok=all(checks.values())
    print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
