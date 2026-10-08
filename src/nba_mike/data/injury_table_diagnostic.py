"""S7.10 evidence-only coordinate/table structure diagnostics. Never edits player rows."""
from __future__ import annotations
import csv, hashlib, json, re
from collections import Counter, defaultdict
from pathlib import Path

FIELDS = ('source_page','source_y','player','status','missing_fields','nearest_above_text','nearest_above_y','nearest_below_text','nearest_below_y','nearby_matchup_text','nearby_matchup_y','nearby_team_text','nearby_team_y','candidate_reason_lines','diagnosis')
LINE_FIELDS = ('page','y','x0','x1','text','words','date_tokens','matchup_tokens','team_tokens','status_tokens','is_header')
DATE = re.compile(r'\b(?:0?[1-9]|1[0-2])/(?:0?[1-9]|[12][0-9]|3[01])/20\d\d\b')
MATCHUP = re.compile(r'\b[A-Z]{2,3}@[A-Z]{2,3}\b')
STATUS = re.compile(r'\b(?:OUT|QUESTIONABLE|DOUBTFUL|PROBABLE|AVAILABLE)\b',re.I)
HEADER = re.compile(r'(?:Player Name|Current Status|Game Date|Matchup|Reason)',re.I)

def group_lines(words, tolerance=2.6):
    """Group PyMuPDF word tuples by vertical center, stable for multi-column PDFs."""
    clusters=[]
    for w in sorted(words,key=lambda z: ((float(z[1])+float(z[3]))/2,float(z[0]))):
        cy=(float(w[1])+float(w[3]))/2
        if clusters and abs(cy-clusters[-1]['cy'])<=tolerance:
            clusters[-1]['words'].append(w)
        else:
            clusters.append({'cy':cy,'words':[w]})
    result=[]
    for cluster in clusters:
        ws=sorted(cluster['words'],key=lambda z:float(z[0]))
        text=' '.join(str(w[4]) for w in ws)
        result.append({'y':round(cluster['cy'],2),'x0':round(min(float(w[0]) for w in ws),2),
                       'x1':round(max(float(w[2]) for w in ws),2),'text':text,'words':ws})
    return result

def summarize_page(page_number, width, height, words, known_teams=()):
    lines=group_lines(words)
    output=[]
    for line in lines:
        t=line['text']
        teams=[team for team in known_teams if re.search(r'(?<!\w)'+re.escape(team)+r'(?!\w)',t,re.I)]
        output.append({'page':page_number,'y':line['y'],'x0':line['x0'],'x1':line['x1'],
                       'text':t,'words':len(line['words']),'date_tokens':len(DATE.findall(t)),
                       'matchup_tokens':len(MATCHUP.findall(t)),'team_tokens':len(teams),
                       'status_tokens':len(STATUS.findall(t)),'is_header':bool(HEADER.search(t))})
    return {'page':page_number,'width':width,'height':height,'lines':output,
            'header_lines':sum(bool(x['is_header']) for x in output),
            'matchup_lines':sum(bool(x['matchup_tokens']) for x in output),
            'team_lines':sum(bool(x['team_tokens']) for x in output),
            'status_lines':sum(bool(x['status_tokens']) for x in output)}

def analyze_rows(rows, pages, reason_traces=()):
    by_page={p['page']:p['lines'] for p in pages}
    traces=defaultdict(list)
    for t in reason_traces:
        try:traces[int(t['source_page'])].append(t)
        except (KeyError,ValueError,TypeError):pass
    diagnostics=[]
    for row in rows:
        missing=[k for k in ('game_date','matchup','team') if not row.get(k)]
        if not missing:continue
        try:p=int(row['source_page']);y=float(row['source_y'])
        except (KeyError,ValueError,TypeError):continue
        lines=by_page.get(p,[])
        above=[line for line in lines if line['y']<=y]
        below=[line for line in lines if line['y']>y]
        prev=above[-1] if above else None
        nxt=below[0] if below else None
        # These are nearby clues, not verified assignments. No propagation.
        match=min((line for line in lines if line['matchup_tokens']),key=lambda z:abs(z['y']-y),default=None)
        team=min((line for line in lines if line['team_tokens']),key=lambda z:abs(z['y']-y),default=None)
        close_traces=[t for t in traces[p] if _near(t,y)]
        diagnosis='NO_PAGE_MATCHUP_TOKEN' if match is None else 'MATCHUP_TOKEN_PRESENT_REQUIRES_VISUAL_REVIEW'
        diagnostics.append({'source_page':p,'source_y':y,'player':row.get('player',''),
          'status':row.get('status',''),'missing_fields':'|'.join(missing),
          'nearest_above_text':prev['text'] if prev else '', 'nearest_above_y':prev['y'] if prev else '',
          'nearest_below_text':nxt['text'] if nxt else '', 'nearest_below_y':nxt['y'] if nxt else '',
          'nearby_matchup_text':match['text'] if match else '', 'nearby_matchup_y':match['y'] if match else '',
          'nearby_team_text':team['text'] if team else '', 'nearby_team_y':team['y'] if team else '',
          'candidate_reason_lines':len(close_traces),'diagnosis':diagnosis})
    return diagnostics

def _near(trace,y):
    try:return abs(float(trace['source_y'])-y)<=22
    except (ValueError,TypeError,KeyError):return False

def read_csv(path):
    with Path(path).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def write_csv(path,fields,rows):
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def run(pdf_path,s77_csv,output_dir,trace_csv=None,render_pages=False):
    import pymupdf
    raw=Path(pdf_path).read_bytes();sha=hashlib.sha256(raw).hexdigest()
    if not raw.startswith(b'%PDF-'):raise ValueError('Not a PDF file')
    rows=read_csv(s77_csv)
    if not rows:raise ValueError('S7.7 CSV contains no records')
    if any(r.get('source_sha256')!=sha for r in rows):raise ValueError('S7.7 source hash does not match PDF')
    traces=read_csv(trace_csv) if trace_csv else []
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    pages=[]; render_paths=[]
    with pymupdf.open(stream=raw,filetype='pdf') as doc:
        for i,page in enumerate(doc,1):
            summary=summarize_page(i,page.rect.width,page.rect.height,page.get_text('words'))
            pages.append(summary)
            if render_pages and any(r.get('source_page')==str(i) and any(not r.get(k) for k in ('game_date','matchup','team')) for r in rows):
                # Page rendering is evidence for a human, not OCR or auto-correction.
                target=out/f'{sha}.page_{i:02d}.png'
                page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4),alpha=False).save(str(target))
                render_paths.append(str(target))
    findings=analyze_rows(rows,pages,traces)
    lines=[line for page in pages for line in page['lines']]
    lp=out/f'{sha}.s7_10_page_lines.csv';fp=out/f'{sha}.s7_10_context_findings.csv'
    write_csv(lp,LINE_FIELDS,lines);write_csv(fp,FIELDS,findings)
    report={'status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','source_sha256':sha,
      'records_read':len(rows),'missing_context_records':len(findings),
      'pages':[{k:v for k,v in p.items() if k!='lines'} for p in pages],
      'findings_by_diagnosis':dict(Counter(x['diagnosis'] for x in findings)),
      'reason_traces_read':len(traces),'original_records_modified':0,
      'historical_publication_verified':False,'eligible_for_asof_training':False,
      'page_lines_csv':str(lp),'context_findings_csv':str(fp),'rendered_pages':render_paths,
      'limitations':['Nearby text is not a verified field assignment',
       'Line clustering may join columns; inspect page PNGs before changing extraction rules',
       'No automated context propagation or training eligibility',
       'PDF publication time is not independently established']}
    jp=out/f'{sha}.s7_10_structure_report.json';jp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report
