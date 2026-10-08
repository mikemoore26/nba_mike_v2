"""Automatic exploratory extraction of one existing local NBA injury PDF."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from nba_mike.data.injury_auto import process_pdf

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--pdf',required=True)
    p.add_argument('--url',required=True)
    p.add_argument('--out',default=str(ROOT/'research/p0_s4/s7_4/results'))
    args=p.parse_args()
    print(json.dumps(process_pdf(args.pdf,args.url,args.out),indent=2))
if __name__=='__main__':main()
