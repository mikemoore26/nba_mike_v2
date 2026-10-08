"""S7.14 multi-PDF generalization audit; strictly research-only.

Inputs are local PDF files; no inferred publication time, no network calls.
"""
from __future__ import annotations
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from .injury_stateful import parse_pages
from .injury_verify import verify

REPORT_FIELDS = ('filename','sha256','pages','players','missing_context','flagged','cross_page_review','spot_check','date_events','matchup_events','team_events','not_submitted_events','duplicate_player_status','status','error')
REVIEW_FIELDS = ('filename','sha256','source_page','player','status','team','matchup','game_date','risk','issues','date_provenance','matchup_provenance','team_provenance')


def _csv(path, fields, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer=csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def audit_pages(pages, sha, filename='fixture.pdf'):
    rows, details=parse_pages(pages, sha)
    events=details['events']
    checks, stats=verify(rows, events)
    counts=Counter(e['type'] for e in events)
    missing=sum(any(not r.get(k) for k in ('game_date','matchup','team')) for r in rows)
    duplicates=Counter((r['source_page'],r['player'],r['status']) for r in rows)
    dup=sum(n-1 for n in duplicates.values() if n>1)
    report={'filename':filename,'sha256':sha,'pages':len(pages),'players':len(rows),
            'missing_context':missing,'flagged':stats['flagged_records'],
            'cross_page_review':stats['cross_page_review'],'spot_check':stats['spot_check'],
            'date_events':counts['DATE'],'matchup_events':counts['MATCHUP'],
            'team_events':counts['TEAM'],'not_submitted_events':counts['NOT_YET_SUBMITTED'],
            'duplicate_player_status':dup,
            'status':'REVIEW_REQUIRED' if missing or stats['flagged_records'] or not rows else 'STRUCTURALLY_CONSISTENT_RESEARCH_ONLY',
            'error':''}
    priority={'FLAGGED':0,'CROSS_PAGE_REVIEW':1,'SPOT_CHECK':2}
    selected=sorted(checks,key=lambda r:(priority.get(r['risk'],3),int(r['source_page']),r['player']))
    sample=[]
    for r in selected[:min(12,len(selected))]:
        sample.append({'filename':filename,'sha256':sha,**r})
    return report,rows,events,checks,sample


def audit_directory(pdf_dir, output_dir, *, min_distinct=3, max_files=30):
    """Audit local PDFs in stable filename order; fail closed on any unreadable PDF.

    min_distinct is a validation gate, not a request to invent additional sources.
    """
    import pymupdf
    root=Path(pdf_dir)
    if not root.is_dir():
        raise ValueError(f'PDF directory not found: {root}')
    if min_distinct<2 or max_files<1:
        raise ValueError('min_distinct must be >=2 and max_files >=1')
    files=sorted(root.glob('*.pdf'))
    if len(files)>max_files:
        raise ValueError(f'{len(files)} PDFs exceed max_files={max_files}; narrow the input directory')
    out=Path(output_dir)
    out.mkdir(parents=True,exist_ok=True)
    reports=[];samples=[];hashes=set();skipped=[]
    for pdf in files:
        raw=pdf.read_bytes()
        sha=hashlib.sha256(raw).hexdigest()
        if sha in hashes:
            skipped.append({'filename':pdf.name,'sha256':sha,'reason':'DUPLICATE_BYTES'})
            continue
        hashes.add(sha)
        if not raw.startswith(b'%PDF-'):
            reports.append({'filename':pdf.name,'sha256':sha,'status':'ERROR','error':'INVALID_PDF_HEADER'})
            continue
        try:
            with pymupdf.open(stream=raw,filetype='pdf') as doc:
                pages=[{'page':i+1,'width':p.rect.width,'words':p.get_text('words')} for i,p in enumerate(doc)]
            report,rows,events,checks,sample=audit_pages(pages,sha,pdf.name)
            reports.append(report);samples.extend(sample)
            _csv(out/f'{sha}.s7_14_candidates.csv',tuple(rows[0].keys()) if rows else ('record_id',),rows)
            _csv(out/f'{sha}.s7_14_events.csv',('page','y','type','value'),events)
            _csv(out/f'{sha}.s7_14_checks.csv',tuple(checks[0].keys()) if checks else ('source_page',),checks)
        except Exception as exc:
            # Do not silently omit failing reports from the denominator.
            reports.append({'filename':pdf.name,'sha256':sha,'status':'ERROR','error':f'{type(exc).__name__}: {exc}'[:250]})
    _csv(out/'s7_14_reports.csv',REPORT_FIELDS,reports)
    _csv(out/'s7_14_review_sample.csv',REVIEW_FIELDS,samples)
    _csv(out/'s7_14_duplicates.csv',('filename','sha256','reason'),skipped)
    errors=sum(r['status']=='ERROR' for r in reports)
    eligible_reports=sum(r['status']=='STRUCTURALLY_CONSISTENT_RESEARCH_ONLY' for r in reports)
    sufficient=len(reports)>=min_distinct and errors==0
    result={'status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING',
            'validation_gate':'READY_FOR_MANUAL_GROUND_TRUTH' if sufficient else 'INSUFFICIENT_DISTINCT_VALID_REPORTS',
            'min_distinct_reports':min_distinct,'distinct_reports':len(reports),
            'duplicate_files_skipped':len(skipped),'reports_with_errors':errors,
            'structurally_consistent_reports':eligible_reports,
            'total_players':sum(r.get('players',0) for r in reports),
            'total_flagged':sum(r.get('flagged',0) for r in reports),
            'total_missing_context':sum(r.get('missing_context',0) for r in reports),
            'historical_publication_verified':False,'eligible_for_asof_training':False,
            'reports_csv':str(out/'s7_14_reports.csv'),
            'review_sample_csv':str(out/'s7_14_review_sample.csv'),
            'limitations':['Structural consistency is not independent extraction accuracy',
                           'At least three distinct PDFs are required before proceeding to manual ground truth',
                           'Source retrieval time and filename do not prove historical publication time',
                           'No record may be used for as-of training']}
    (out/'s7_14_report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
