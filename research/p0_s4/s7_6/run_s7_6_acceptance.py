import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable,'-m','pytest','-q',str(root/'tests/test_injury_layout_s76.py')]))
