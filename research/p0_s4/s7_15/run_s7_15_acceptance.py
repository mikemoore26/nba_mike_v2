import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable,'-m','pytest','-q',str(ROOT/'tests/test_injury_acquire_s715.py')],cwd=ROOT))
