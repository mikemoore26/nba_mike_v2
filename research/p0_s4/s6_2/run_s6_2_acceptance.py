import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3]
r=subprocess.run([sys.executable,'-m','pytest','tests/test_conditional_uncertainty.py','-q'],cwd=root)
print('S6.2 ACCEPTANCE', 'PASS' if r.returncode==0 else 'FAIL')
raise SystemExit(r.returncode)
