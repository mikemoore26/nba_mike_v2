import subprocess
import sys
from pathlib import Path

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[3]
    cmd = [sys.executable, '-m', 'pytest', 'tests/test_role_aware_uncertainty.py', '-q']
    result = subprocess.run(cmd, cwd=root)
    print('S6.1 TESTS', 'PASS' if result.returncode == 0 else 'FAIL')
    print('OVERALL', 'PASS' if result.returncode == 0 else 'FAIL')
    raise SystemExit(result.returncode)
