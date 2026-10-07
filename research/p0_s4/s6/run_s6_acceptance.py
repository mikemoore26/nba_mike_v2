import subprocess,sys
from pathlib import Path
def main():
    root=Path(__file__).resolve().parents[3]
    result=subprocess.run([sys.executable,"-m","pytest","tests/test_minutes_uncertainty.py","-q"],cwd=root)
    print("s6_tests", "PASS" if result.returncode==0 else "FAIL")
    print("OVERALL", "PASS" if result.returncode==0 else "FAIL")
    return result.returncode
if __name__=="__main__":raise SystemExit(main())
