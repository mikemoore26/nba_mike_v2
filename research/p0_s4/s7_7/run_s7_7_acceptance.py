import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable,'-m','pytest','-q',str(ROOT/'tests/test_injury_layout_s77.py')],cwd=ROOT))
