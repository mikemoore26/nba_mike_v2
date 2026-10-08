import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from nba_mike.data.injury_table_diagnostic import run
p=argparse.ArgumentParser(description='S7.10 PDF table-structure evidence audit')
p.add_argument('--pdf',type=Path,required=True)
p.add_argument('--s77',type=Path,required=True)
p.add_argument('--traces',type=Path)
p.add_argument('--output-dir',type=Path,default=ROOT/'research/p0_s4/s7_10/results')
p.add_argument('--render-pages',action='store_true')
a=p.parse_args()
print(json.dumps(run(a.pdf,a.s77,a.output_dir,a.traces,a.render_pages),indent=2))
