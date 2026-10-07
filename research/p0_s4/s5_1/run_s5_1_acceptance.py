from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[3]
checks={
 'tests':subprocess.run([sys.executable,'-m','pytest','tests/test_s5_1_robustness.py','-q'],cwd=root).returncode==0,
 'runner':(root/'research/p0_s4/s5_1/run_s5_1.py').is_file(),
 'documentation':(root/'docs/S5_1_ROBUSTNESS_STANDARD.md').is_file(),
}
for k,v in checks.items():print(k,'PASS' if v else 'FAIL')
print('OVERALL','PASS' if all(checks.values()) else 'FAIL')
raise SystemExit(0 if all(checks.values()) else 1)
