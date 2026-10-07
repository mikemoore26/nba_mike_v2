import subprocess
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[3]
subprocess.run([sys.executable,'-m','pytest','tests/test_s6_3_diagnostics.py','-q'],cwd=root,check=True)
print('S6.3 ACCEPTANCE PASS')
