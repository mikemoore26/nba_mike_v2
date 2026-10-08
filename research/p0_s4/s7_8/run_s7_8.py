import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from nba_mike.data.injury_audit import load_csv,audit,write_report
p=argparse.ArgumentParser(description='S7.8 read-only cross-parser audit')
p.add_argument('--sha',required=True)
p.add_argument('--s74',type=Path,required=True)
p.add_argument('--s76',type=Path,required=True)
p.add_argument('--s77',type=Path,required=True)
p.add_argument('--sample-size',type=int,default=12)
p.add_argument('--output-dir',type=Path,default=ROOT/'research/p0_s4/s7_8/results')
a=p.parse_args()
report=audit(load_csv(a.s74),load_csv(a.s76),load_csv(a.s77),a.sha,a.sample_size)
paths=write_report(report,a.output_dir)
print(json.dumps({k:v for k,v in report.items() if k not in ('missing_date_records','disagreements','review_sample')}|{'output_json':str(paths[0]),'review_sample_csv':str(paths[1])},indent=2))
