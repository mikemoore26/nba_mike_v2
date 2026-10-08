"""S7.21 independent source-coordinate context checks; research only."""
from __future__ import annotations
import argparse,csv,hashlib,json,re
from pathlib import Path

FIELDS=['source_sha256','record_id','page','player','field','assigned','source_text','source_page','source_y','verdict','detail']
PROV=re.compile(r'^EXPLICIT:p(\d+):y([0-9.]+)$')

def read_csv(p):
    with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def audit(pdf_dir,results_dir,out_dir):
    import pymupdf
    pdf_dir=Path(pdf_dir);results_dir=Path(results_dir);out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
    detail=[]; summary={'milestone':'S7.21','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','reports':0,'records':0,'field_checks':0,'verified':0,'mismatches':0,'unresolved':0,'cross_page_checks':0,'cross_page_verified':0,'missing_pdf':[],'historical_publication_verified':False,'eligible_for_asof_training':False}
    for csvfile in sorted(results_dir.glob('*.s7_14_candidates.csv')):
        sha=csvfile.name.split('.')[0];pdf=pdf_dir/(sha+'.pdf'); rows=read_csv(csvfile)
        if not pdf.exists():summary['missing_pdf'].append(sha);continue
        if hashlib.sha256(pdf.read_bytes()).hexdigest()!=sha:raise ValueError('PDF SHA mismatch '+sha)
        summary['reports']+=1;summary['records']+=len(rows)
        with pymupdf.open(pdf) as doc:
            pages=[[{'x':w[0],'y':(w[1]+w[3])/2,'text':w[4]} for w in p.get_text('words')] for p in doc]
        for r in rows:
            rp=int(r['source_page']);ry=float(r['source_y'])
            for field,lo,hi,prov in [('game_date',0,115,'date_provenance'),('matchup',195,260,'matchup_provenance'),('team',260,420,'team_provenance')]:
                summary['field_checks']+=1
                m=PROV.fullmatch(r[prov]);source='';verdict='UNRESOLVED';detail_msg='missing or invalid provenance'
                sp=sy=None
                if m:
                    sp=int(m.group(1));sy=float(m.group(2))
                    if 1<=sp<=len(pages) and (sp<rp or (sp==rp and sy<=ry+.05)):
                        # Independently extract words from PDF by physical column and provenance row.
                        ws=sorted((w for w in pages[sp-1] if lo<=w['x']<hi and abs(w['y']-sy)<=3.1),key=lambda w:w['x'])
                        source=' '.join(w['text'] for w in ws)
                        if field=='game_date':
                            mm=re.search(r'(\d{2})/(\d{2})/(\d{4})',source)
                            observed=f'{mm.group(3)}-{mm.group(1)}-{mm.group(2)}' if mm else ''
                        else:observed=source.strip()
                        if observed==r[field]:verdict='VERIFIED';detail_msg='PDF lane text matches recorded explicit anchor'
                        elif not observed:detail_msg='no text in expected lane at anchor'
                        else:verdict='MISMATCH';detail_msg='PDF lane differs from assigned value'
                        if sp<rp:summary['cross_page_checks']+=1;summary['cross_page_verified']+=verdict=='VERIFIED'
                    else:detail_msg='provenance anchor after record or outside PDF'
                summary['verified']+=verdict=='VERIFIED';summary['mismatches']+=verdict=='MISMATCH';summary['unresolved']+=verdict=='UNRESOLVED'
                detail.append({'source_sha256':sha,'record_id':r['record_id'],'page':rp,'player':r['player'],'field':field,'assigned':r[field],'source_text':source,'source_page':sp or '', 'source_y':sy if sy is not None else '', 'verdict':verdict,'detail':detail_msg})
    summary['records_expected']=475
    summary['source_context_gate']='PASS_STRUCTURAL_COORDINATES' if summary['reports']==5 and summary['records']==475 and summary['mismatches']==0 and summary['unresolved']==0 else 'REVIEW_REQUIRED'
    summary['limitations']=['PDF coordinate agreement is not independent human ground truth','Player identity, matchup-to-team semantic validity, missing-row recall, and original publication timing require separate evidence','No source records modified']
    with (out_dir/'s7_21_context_checks.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(detail)
    (out_dir/'s7_21_report.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return summary

def main():
    p=argparse.ArgumentParser();p.add_argument('--pdf-dir',default='research/p0_s4/s7_14/input_pdfs');p.add_argument('--results-dir',default='research/p0_s4/s7_14/results');p.add_argument('--output-dir',default='research/p0_s4/s7_21/results');a=p.parse_args()
    print(json.dumps(audit(a.pdf_dir,a.results_dir,a.output_dir),indent=2))
if __name__=='__main__':main()
