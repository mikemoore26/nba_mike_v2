"""S7.16 blinded, stratified human ground-truth packet for injury PDFs.

Does not call the parser, certify historical publication, or infer truth from its own outputs.
"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path

FIELDS=('sample_id','sha256','source_file','source_page','source_y','player','status','team','matchup','game_date','reason','risk','review_player','review_status','review_team','review_matchup','review_game_date','review_reason','review_notes')
REVIEW=('sample_id','player_correct','status_correct','team_correct','matchup_correct','game_date_correct','reason_correct','notes')


def choose(rows, per_report=4):
    """Deterministic risk-balanced sample; no RNG, no outcome-dependent choices."""
    if per_report<1:raise ValueError('per_report must be positive')
    by={}
    for r in rows:
        by.setdefault(r['sha256'],[]).append(r)
    result=[]
    for sha,group in sorted(by.items()):
        if not group:continue
        def key(r):
            inherited=sum(str(r.get(f+'_provenance','')).startswith('EXPLICIT:p') and
                          not str(r.get(f+'_provenance','')).startswith('EXPLICIT:p'+str(r.get('source_page'))+':')
                          for f in ('date','matchup','team'))
            return (-inherited, -int(float(r['source_page'])),hashlib.sha256((sha+'|'+str(r['source_page'])+'|'+r['player']).encode()).hexdigest())
        ordered=sorted(group,key=key)
        chosen=[];pages=set()
        for r in ordered:
            if r['source_page'] not in pages:
                chosen.append(r);pages.add(r['source_page'])
                if len(chosen)>=per_report:break
        for r in ordered:
            if len(chosen)>=per_report:break
            if r not in chosen:chosen.append(r)
        result.extend(chosen)
    return result


def _write(path,fields,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)


def build_packet(pdf_dir, candidates_dir, output_dir, per_report=4):
    import pymupdf
    pdf_dir=Path(pdf_dir);candidates_dir=Path(candidates_dir);out=Path(output_dir)
    if not pdf_dir.is_dir() or not candidates_dir.is_dir():raise ValueError('input directories missing')
    if not 1<=per_report<=20:raise ValueError('per_report must be 1..20')
    out.mkdir(parents=True,exist_ok=True)
    rows=[];sources=[]
    for pdf in sorted(pdf_dir.glob('*.pdf')):
        raw=pdf.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        candidate=candidates_dir/(sha+'.s7_14_candidates.csv')
        if not candidate.is_file():raise ValueError('Missing candidates for '+sha)
        with candidate.open(newline='',encoding='utf-8-sig') as f:items=list(csv.DictReader(f))
        if not items or any(r.get('source_sha256')!=sha for r in items):raise ValueError('Candidate SHA mismatch: '+sha)
        with pymupdf.open(stream=raw,filetype='pdf') as doc:
            n=len(doc)
        for r in items:
            page=int(r['source_page']);y=float(r['source_y'])
            if page<1 or page>n or y<0:raise ValueError('Invalid page or y coordinate')
            rows.append({**r,'sha256':sha,'source_file':pdf.name})
        sources.append({'sha256':sha,'file':pdf.name,'pages':n,'candidates':len(items)})
    sample=choose(rows,per_report)
    packet=[]
    for i,r in enumerate(sample,1):
        sid=f'GT{i:03d}'
        packet.append({**r,'sample_id':sid,'risk':'CROSS_PAGE' if any('EXPLICIT:p'+str(r['source_page'])+':' not in str(r.get(k+'_provenance','')) for k in ('date','matchup','team')) else 'SAME_PAGE',
                       **{k:'' for k in ('review_player','review_status','review_team','review_matchup','review_game_date','review_reason','review_notes')}})
    _write(out/'s7_16_samples.csv',FIELDS,packet)
    _write(out/'s7_16_blind_review.csv',REVIEW,[{'sample_id':r['sample_id']} for r in packet])
    # Crops are *source* PDF pixels, not reconstructed data. Wider page context avoids misleading snippets.
    for r in packet:
        pdf=pdf_dir/r['source_file']
        with pymupdf.open(pdf) as doc:
            p=doc[int(r['source_page'])-1];y=float(r['source_y'])
            rect=p.rect
            crop=pymupdf.Rect(rect.x0,max(rect.y0,y-115),rect.x1,min(rect.y1,y+65))
            pix=p.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),clip=crop,alpha=False)
            pix.save(out/(r['sample_id']+'.png'))
    summary={'status':'AWAITING_INDEPENDENT_GROUND_TRUTH','decision':'BLOCK_TRAINING','distinct_reports':len(sources),
             'candidate_records':len(rows),'sampled_records':len(packet),'per_report_target':per_report,
             'independent_review_completed':0,'historical_publication_verified':False,'eligible_for_asof_training':False,
             'limitations':['Samples and crops come from the source PDF but the sample fields are parser predictions',
                            'Automated consistency checks are not independent truth',
                            'Reviewers must compare images to predictions; blank review cells are not passes',
                            'Source availability at historical report time is not established']}
    (out/'s7_16_report.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return summary


def grade(samples_csv,review_csv):
    """Fail-closed grading: require an explicit YES/NO/UNREADABLE for every field."""
    with Path(samples_csv).open(newline='',encoding='utf-8-sig') as f:samples=list(csv.DictReader(f))
    with Path(review_csv).open(newline='',encoding='utf-8-sig') as f:reviews=list(csv.DictReader(f))
    ids=[r['sample_id'] for r in samples]
    if len(ids)!=len(set(ids)) or set(ids)!={r['sample_id'] for r in reviews} or len(ids)!=len(reviews):
        raise ValueError('Sample/review IDs do not match exactly')
    fields=[k for k in REVIEW if k.endswith('_correct')]
    counts={f:{'YES':0,'NO':0,'UNREADABLE':0,'PENDING':0} for f in fields}
    for row in reviews:
        for f in fields:
            v=(row.get(f) or '').strip().upper()
            if v not in ('YES','NO','UNREADABLE',''):
                raise ValueError(f'Invalid {f}: {v}')
            counts[f][v or 'PENDING']+=1
    complete=all(v['PENDING']==0 for v in counts.values())
    return {'status':'REVIEW_COMPLETE' if complete else 'REVIEW_PENDING','decision':'BLOCK_TRAINING',
            'sampled_records':len(ids),'field_counts':counts,'historical_publication_verified':False,
            'eligible_for_asof_training':False}
