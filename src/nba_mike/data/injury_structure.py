"""S7.3: conservative extraction of candidate rows; no training eligibility.

Text extraction is not a substitute for a verified NBA report schema.
"""
from __future__ import annotations
import csv, hashlib, json, re
from pathlib import Path
from .injury_pdf import extract_pdf_text
from .injury_asof import parse_official_url, verify_pdf_bytes

STATUS = re.compile(r'\b(Out|Doubtful|Questionable|Probable|Available)\b',re.I)
DATE = re.compile(r'\b\d{4}-\d{2}-\d{2}\b')
TIME = re.compile(r'\b\d{1,2}:\d{2}\s*(?:AM|PM|ET)\b',re.I)
FIELDS=('candidate_id','source_sha256','source_page','source_line','raw_text','status_token','review_status','game_date','matchup','team','player','reason')

def candidates_from_pages(pages, sha):
    """Do not guess team/player from neighboring PDF lines or page headers."""
    out=[]
    for page in pages:
        for i,line in enumerate(page['text'].splitlines(),1):
            match=STATUS.search(line)
            if not match: continue
            raw=line.strip()
            if not raw: continue
            ident=hashlib.sha256(f'{sha}|{page["page"]}|{i}|{raw}'.encode()).hexdigest()[:20]
            out.append(dict(candidate_id=ident,source_sha256=sha,source_page=page['page'],source_line=i,
                raw_text=raw,status_token=match.group(1).upper(),review_status='UNREVIEWED',
                game_date='',matchup='',team='',player='',reason=''))
    return out

def build_review(pdf_path, source_url, output_dir):
    parse_official_url(source_url)
    data=Path(pdf_path).read_bytes();sha=verify_pdf_bytes(data)
    pages=extract_pdf_text(data)
    rows=candidates_from_pages(pages,sha)
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    csv_path=out/(sha+'.review.csv')
    # A manual review template, not structured truth.
    with csv_path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
    manifest={'status':'MANUAL_REVIEW_REQUIRED','sha256':sha,'source_url':source_url,
        'pdf_path':str(pdf_path),'pages':len(pages),'candidate_lines':len(rows),
        'review_csv':str(csv_path),'eligible_for_asof_training':False,
        'historical_publication_verified':False,
        'limitations':['Text status matches may include headers, reasons, or continuation lines',
        'No automatic player/team/matchup assignment','Human-reviewed records still require historical publication verification']}
    (out/(sha+'.review_manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest

def validate_review(review_csv, source_sha256, *, min_checked=10):
    """Assess manual review completeness; never authorize training."""
    with Path(review_csv).open(newline='',encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    ids=set(); problems=[];checked=0;accepted=0
    for idx,r in enumerate(rows,2):
        cid=r.get('candidate_id','')
        if not cid or cid in ids: problems.append(f'line {idx}: missing/duplicate candidate_id')
        ids.add(cid)
        if r.get('source_sha256')!=source_sha256: problems.append(f'line {idx}: source hash mismatch')
        decision=r.get('review_status','')
        if decision not in ('UNREVIEWED','CONFIRMED','REJECTED','AMBIGUOUS'):
            problems.append(f'line {idx}: invalid review_status')
        if decision in ('CONFIRMED','REJECTED','AMBIGUOUS'): checked+=1
        if decision=='CONFIRMED':
            accepted+=1
            for key in ('game_date','team','player','reason'):
                if not r.get(key,'').strip():problems.append(f'line {idx}: confirmed missing {key}')
            if r.get('game_date') and not re.fullmatch(r'\d{4}-\d{2}-\d{2}',r['game_date']):
                problems.append(f'line {idx}: invalid game_date')
    return {'status':'RESEARCH_ONLY','rows':len(rows),'reviewed':checked,'confirmed':accepted,
        'unreviewed':len(rows)-checked,'minimum_review_met':checked>=min_checked,
        'review_validation_passed':not problems and checked>=min_checked,
        'problems':problems,'eligible_for_asof_training':False}
