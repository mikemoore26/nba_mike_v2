from pathlib import Path
import argparse,json
from nba_mike.data.injury_ground_truth import build_packet,grade
ROOT=Path(__file__).resolve().parents[3]
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--pdf-dir',type=Path,default=ROOT/'research/p0_s4/s7_14/input_pdfs')
    p.add_argument('--candidates-dir',type=Path,default=ROOT/'research/p0_s4/s7_14/results')
    p.add_argument('--output-dir',type=Path,default=ROOT/'research/p0_s4/s7_16/results')
    p.add_argument('--per-report',type=int,default=4)
    p.add_argument('--grade',action='store_true')
    a=p.parse_args()
    if a.grade:
        report=grade(a.output_dir/'s7_16_samples.csv',a.output_dir/'s7_16_blind_review.csv')
        (a.output_dir/'s7_16_grade.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    else:report=build_packet(a.pdf_dir,a.candidates_dir,a.output_dir,a.per_report)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
