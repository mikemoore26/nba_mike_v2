import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable,'-m','pytest',str(root/'tests'/'test_injury_asof.py'),'-q'],cwd=root))
