"""S7.14 multi-report local PDF audit."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from nba_mike.data.injury_multi_report import audit_directory
p=argparse.ArgumentParser()
p.add_argument('--pdf-dir',type=Path,default=ROOT/'research/p0_s4/s7_14/input_pdfs')
p.add_argument('--output-dir',type=Path,default=ROOT/'research/p0_s4/s7_14/results')
p.add_argument('--min-distinct',type=int,default=3)
p.add_argument('--max-files',type=int,default=30)
a=p.parse_args()
print(json.dumps(audit_directory(a.pdf_dir,a.output_dir,min_distinct=a.min_distinct,max_files=a.max_files),indent=2))
