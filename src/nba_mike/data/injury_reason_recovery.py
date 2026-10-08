"""S7.17: conservative, auditable reason recovery from PDF word geometry.

Never changes source candidates, never certifies publication timing, never trains.
"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path

FIELDS=('record_id','source_sha256','source_page','source_y','player','status','old_reason','proposed_reason','decision','evidence_y_min','evidence_y_max','notes')


def recover_page(rows, words, width=841.95):
    """Propose reason for blank-reason rows only; refuse uncertain geometry.

    The PDF has a fixed reason lane beginning at x=665 on a width=841.95 page.
    Each row's y is a center-of-text anchor. A recovery needs a reason prefix
    within a guarded two-line band around the player anchor.
    """
    boundary=665.0*float(width)/841.95
    ordered=sorted(rows,key=lambda r:float(r['source_y']))
    proposals=[]
    for i,r in enumerate(ordered):
        base={'record_id':r.get('record_id',''),'source_sha256':r.get('source_sha256',''),
              'source_page':r['source_page'],'source_y':r['source_y'],
              'player':r['player'],'status':r['status'],'old_reason':r.get('reason',''),
              'proposed_reason':'','decision':'UNCHANGED','evidence_y_min':'','evidence_y_max':'','notes':''}
        if (r.get('reason') or '').strip():
            proposals.append(base);continue
        y=float(r['source_y'])
        prev_y=float(ordered[i-1]['source_y']) if i else float('-inf')
        next_y=float(ordered[i+1]['source_y']) if i+1<len(ordered) else float('inf')
        # NBA PDFs center the player/status text BETWEEN two reason lines,
        # at approximately -7 and +7 PDF points. Midpoints isolate neighbors.
        floor=max(y-12,(prev_y+y)/2)
        ceiling=min(y+12,(y+next_y)/2)
        candidates=[w for w in words if float(w[0])>=boundary and
                    floor<=((float(w[1])+float(w[3]))/2)<ceiling]
        if not candidates:
            base.update(decision='UNRESOLVED',notes='No unambiguous words in reason lane')
            proposals.append(base);continue
        # Group into physical lines; keep text order and preserve wrapped reasons.
        lines=[]
        for w in sorted(candidates,key=lambda w:((float(w[1])+float(w[3]))/2,float(w[0]))):
            cy=(float(w[1])+float(w[3]))/2
            if not lines or abs(cy-lines[-1][0])>3:
                lines.append((cy,[w]))
            else:lines[-1][1].append(w)
        # The first reason line may be above the player, but require a tight
        # upper/anchor line and an explicit recognized reason prefix.
        if not (y-10<=lines[0][0]<=y+4):
            base.update(decision='UNRESOLVED',notes='No reason prefix near player anchor')
            proposals.append(base);continue
        text=' '.join(' '.join(str(w[4]) for w in sorted(ws,key=lambda z:float(z[0]))) for _,ws in lines).strip()
        # NBA reason prefixes; avoid filling from headers, stray page text or another row.
        allowed=('Injury/Illness -','G League -','Personal Reasons','Not With Team','Suspension',
                 'Rest','Health and Safety','League Suspension','Return to Competition')
        if not text.startswith(allowed):
            base.update(decision='UNRESOLVED',notes='Reason prefix not recognized')
        else:
            base.update(decision='PROPOSED_REVIEW_REQUIRED',proposed_reason=text,
                        evidence_y_min=round(min(float(w[1]) for w in candidates),2),
                        evidence_y_max=round(max(float(w[3]) for w in candidates),2),
                        notes='Geometry proposal; compare to original PDF before approval')
        proposals.append(base)
    return proposals


def run(pdf_dir,candidates_dir,output_dir):
    import pymupdf
    pdf_dir=Path(pdf_dir);candidates_dir=Path(candidates_dir);out=Path(output_dir)
    if not pdf_dir.is_dir() or not candidates_dir.is_dir():raise ValueError('Missing PDF/candidate directory')
    out.mkdir(parents=True,exist_ok=True)
    results=[];sources=[]
    for pdf in sorted(pdf_dir.glob('*.pdf')):
        raw=pdf.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        candidate=candidates_dir/f'{sha}.s7_14_candidates.csv'
        if not candidate.is_file():raise ValueError(f'Missing S7.14 candidate file for {sha}')
        with candidate.open(newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
        if not rows or any(r.get('source_sha256')!=sha for r in rows):raise ValueError('Source SHA mismatch')
        with pymupdf.open(stream=raw,filetype='pdf') as doc:
            pages={i+1:(p.get_text('words'),p.rect.width) for i,p in enumerate(doc)}
        grouped={}
        for r in rows:
            page=int(r['source_page'])
            if page not in pages:raise ValueError('Candidate page outside PDF')
            grouped.setdefault(page,[]).append(r)
        for page,group in grouped.items():
            words,width=pages[page]
            results.extend(recover_page(group,words,width))
        sources.append({'sha256':sha,'records':len(rows)})
    path=out/'s7_17_reason_proposals.csv'
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='ignore');writer.writeheader();writer.writerows(results)
    counts={k:sum(r['decision']==k for r in results) for k in ('UNCHANGED','PROPOSED_REVIEW_REQUIRED','UNRESOLVED')}
    summary={'status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','distinct_reports':len(sources),
             'records':len(results),'reason_recovery':counts,'source_records_modified':0,
             'historical_publication_verified':False,'eligible_for_asof_training':False,
             'proposals_csv':str(path),
             'limitations':['Geometry proposals are not independent ground truth',
                            'Proposed reason strings require visual verification',
                            'Missing-row recall and historical publication timing are not established']}
    (out/'s7_17_report.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return summary
