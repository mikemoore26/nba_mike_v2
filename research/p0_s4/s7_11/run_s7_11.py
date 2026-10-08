import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from nba_mike.data.injury_stateful import run
p=argparse.ArgumentParser(description='S7.11 document-wide stateful NBA injury table research parser')
p.add_argument('--pdf',type=Path,required=True)
p.add_argument('--s77',type=Path,required=True)
p.add_argument('--output-dir',type=Path,default=ROOT/'research/p0_s4/s7_11/results')
a=p.parse_args()
print(json.dumps(run(a.pdf,a.s77,a.output_dir),indent=2))
