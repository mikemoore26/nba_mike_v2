import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from nba_mike.data.injury_verify import run
p=argparse.ArgumentParser()
p.add_argument('--pdf',type=Path,required=True)
p.add_argument('--candidates',type=Path,required=True)
p.add_argument('--events',type=Path,required=True)
p.add_argument('--output-dir',type=Path,default=ROOT/'research/p0_s4/s7_12/results')
a=p.parse_args()
print(json.dumps(run(a.pdf,a.candidates,a.events,a.output_dir),indent=2))
