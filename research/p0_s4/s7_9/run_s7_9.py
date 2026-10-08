import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from nba_mike.data.injury_context_audit import audit_pdf
p=argparse.ArgumentParser(description='S7.9 evidence-only PDF context/orphan audit')
p.add_argument('--pdf',type=Path,required=True)
p.add_argument('--url',required=True)
p.add_argument('--s77',type=Path,required=True)
p.add_argument('--output-dir',type=Path,default=ROOT/'research/p0_s4/s7_9/results')
a=p.parse_args()
print(json.dumps(audit_pdf(a.pdf,a.url,a.s77,a.output_dir),indent=2))
