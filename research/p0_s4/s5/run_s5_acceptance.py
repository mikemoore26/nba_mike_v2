"""Offline S5 acceptance checks."""
import subprocess,sys
from pathlib import Path

def main():
    root=Path(__file__).resolve().parents[3]
    cmd=[sys.executable,"-m","pytest","tests/test_adaptive_form.py","-q"]
    rc=subprocess.call(cmd,cwd=root)
    checks={"s5_unit_tests":rc==0,
            "runner_present":(root/"research/p0_s4/s5/run_s5.py").exists(),
            "standard_present":(root/"docs/S5_ADAPTIVE_FORM_RESEARCH.md").exists()}
    for k,v in checks.items():print(k,"PASS" if v else "FAIL")
    print("OVERALL", "PASS" if all(checks.values()) else "FAIL")
    return 0 if all(checks.values()) else 1
if __name__=="__main__":raise SystemExit(main())
