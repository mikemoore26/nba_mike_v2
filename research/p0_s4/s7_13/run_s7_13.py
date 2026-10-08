"""Run corrected S7.12 validator, writing S7.13-specific research outputs."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from nba_mike.data.injury_verify import run
p=argparse.ArgumentParser()
p.add_argument('--pdf',type=Path,required=True)
p.add_argument('--candidates',type=Path,required=True)
p.add_argument('--events',type=Path,required=True)
p.add_argument('--output-dir',type=Path,default=ROOT/'research/p0_s4/s7_13/results')
a=p.parse_args()
result=run(a.pdf,a.candidates,a.events,a.output_dir)
print(json.dumps(result,indent=2))
