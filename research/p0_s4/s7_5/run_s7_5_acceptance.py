import subprocess,sys
raise SystemExit(subprocess.call([sys.executable,'-m','pytest','-q','tests/test_injury_layout.py']))
