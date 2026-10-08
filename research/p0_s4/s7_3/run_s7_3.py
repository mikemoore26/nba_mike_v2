"""S7.3 offline review worksheet generation and review validation."""
import argparse,json
from pathlib import Path
from nba_mike.data.injury_structure import build_review,validate_review

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pdf',type=Path);ap.add_argument('--url')
    ap.add_argument('--review-csv',type=Path);ap.add_argument('--sha256');ap.add_argument('--min-checked',type=int,default=10)
    ap.add_argument('--output',type=Path,default=Path('research/p0_s4/s7_3/results'))
    a=ap.parse_args()
    if a.review_csv:
        if not a.sha256: ap.error('--review-csv requires --sha256')
        result=validate_review(a.review_csv,a.sha256,min_checked=a.min_checked)
    elif a.pdf and a.url:
        result=build_review(a.pdf,a.url,a.output)
    elif a.pdf or a.url: ap.error('provide --pdf and --url together')
    else:
        print('S7.3 READY: provide --pdf and --url for offline candidate review worksheet');return
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
