import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from nba_mike.data.injury_layout import process_pdf
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);p.add_argument('--url',required=True)
a=p.parse_args()
print(json.dumps(process_pdf(a.pdf,a.url,ROOT/'research/p0_s4/s7_5/results'),indent=2))
