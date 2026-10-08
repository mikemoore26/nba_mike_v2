"""Acquire a single official report only when explicitly given --url; otherwise offline audit."""
import argparse, json
from pathlib import Path
from nba_mike.data.injury_pdf import acquire_and_audit

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--url', help='Exact official NBA injury PDF URL; enables network acquisition')
    ap.add_argument('--pdf',type=Path,help='Optional local official PDF, paired with --url')
    ap.add_argument('--output',type=Path,default=Path('research/p0_s4/s7_2/results'))
    args=ap.parse_args()
    if args.pdf and not args.url: ap.error('--pdf requires --url for provenance')
    if not args.url:
        print('S7.2 READY — no download performed; supply --url for one explicit report')
        return
    report=acquire_and_audit(args.url,args.output,data=args.pdf.read_bytes() if args.pdf else None)
    print(json.dumps({k:v for k,v in report.items() if k!='status_line_candidates'},indent=2))
    print('candidate lines:',len(report['status_line_candidates']))
    print('RESEARCH ONLY: no as-of/training authorization')
if __name__=='__main__': main()
