"""S7.5 exploratory coordinate-aware NBA injury PDF parser.

Research only. Never infer historical publication from filename or PDF contents.
"""
from __future__ import annotations
import csv, hashlib, json, re
from pathlib import Path
from .injury_auto import TEAMS, STATUS, DATE, MATCHUP, PLAYER

HEADERS = ('game date', 'game time', 'matchup', 'team', 'player name', 'current status', 'reason')
FIELDS = ('record_id','source_sha256','source_page','source_y','game_date','date_provenance','matchup','team','player','status','reason','parse_status','flags','eligible_for_asof_training')


def word_lines(words, tolerance=3.0):
    """Group word tuples (x0,y0,x1,y1,text,...) into physical lines."""
    ordered=sorted(words,key=lambda w:(round(float(w[1])/tolerance),float(w[0])))
    lines=[]
    for w in ordered:
        y=(float(w[1])+float(w[3]))/2
        # choose closest existing line within tolerance
        choices=[l for l in lines if abs(l['y']-y)<=tolerance]
        if choices:
            target=min(choices,key=lambda l:abs(l['y']-y))
        else:
            target={'y':y,'words':[]};lines.append(target)
        target['words'].append(w)
    for l in lines:l['words'].sort(key=lambda w:float(w[0]))
    return sorted(lines,key=lambda l:l['y'])


def infer_columns(lines):
    """Find NBA report column positions from header word coordinates; fail closed."""
    for l in lines[:25]:
        ws=l['words']; t=' '.join(str(w[4]) for w in ws).lower()
        if 'player' not in t or 'status' not in t or 'reason' not in t:continue
        starts={}
        for w in ws:
            v=str(w[4]).lower().strip(':')
            if v in ('player','status','reason','team','matchup'):
                starts[v]=float(w[0])
        if all(k in starts for k in ('player','status','reason')) and starts['player']<starts['status']<starts['reason']:
            return starts
    return None


def cells(line, columns):
    """Assign by word center, using header-derived column boundaries."""
    keys=sorted(columns,key=lambda k:columns[k]); boundaries={}
    for i,k in enumerate(keys):
        boundaries[k]= (columns[keys[i-1]]+columns[k])/2 if i else float('-inf')
    out={k:[] for k in keys}
    for w in line['words']:
        x=(float(w[0])+float(w[2]))/2
        k=keys[0]
        for kk in keys:
            if x>=boundaries[kk]:k=kk
        out[k].append(str(w[4]))
    return {k:' '.join(v).strip() for k,v in out.items()}


def parse_word_pages(pages, sha):
    """Parse table-like words across pages; never silently inherit game context.

    Header coordinates can be reused only when page width is compatible. A
    fallback header is a layout hint, NOT proof of team/date/matchup context.
    """
    rows=[]
    diagnostics={'pages_without_header':[], 'pages_using_inherited_columns':[],
                 'pages_layout_mismatch':[], 'continuation_lines':0,
                 'orphan_continuations':0, 'per_page':[], 'document_dates':[], 'date_backfills':0, 'date_conflicts':False}
    previous_columns=None
    previous_width=None
    for p in pages:
        page_no=p['page']; lines=word_lines(p['words']); own_columns=infer_columns(lines)
        width=p.get('width')
        compatible=(width is None or previous_width is None or
                    abs(float(width)-float(previous_width))<=2.0)
        if own_columns:
            columns=own_columns
            previous_columns=own_columns
            previous_width=width
            mode='DETECTED_HEADER'
        elif previous_columns and compatible:
            columns=previous_columns
            mode='REUSED_COLUMNS'
            diagnostics['pages_without_header'].append(page_no)
            diagnostics['pages_using_inherited_columns'].append(page_no)
        else:
            diagnostics['pages_without_header'].append(page_no)
            if previous_columns and not compatible:
                diagnostics['pages_layout_mismatch'].append(page_no)
            diagnostics['per_page'].append({'page':page_no,'mode':'SKIPPED_NO_SAFE_COLUMNS',
                'records':0,'complete':0,'review_required':0})
            continue
        ctx={'game_date':'','matchup':'','team':''}
        last=None
        page_rows=[]
        for line in lines:
            txt=' '.join(str(w[4]) for w in line['words'])
            if 'player' in txt.lower() and 'status' in txt.lower() and 'reason' in txt.lower():
                last=None
                continue
            d=DATE.search(txt)
            if d:
                mm,dd,yyyy=d.group(1).split('/')
                ctx['game_date']=f'{yyyy}-{mm}-{dd}'
            m=MATCHUP.search(txt)
            if m:ctx['matchup']=m.group(0)
            matches=[t for t in TEAMS if re.search(r'(?<!\w)'+re.escape(t)+r'(?!\w)',txt)]
            if len(matches)==1:ctx['team']=matches[0]
            # A new matchup without a named team must not retain previous game's team.
            if m and not matches:ctx['team']=''
            c=cells(line,columns)
            player_text=c.get('player','');status_text=c.get('status','');reason_text=c.get('reason','')
            sm=STATUS.search(status_text)
            nm=PLAYER.search(player_text)
            if sm and nm:
                name=nm.group(2)+' '+nm.group(1)
                rid=hashlib.sha256(f'{sha}|{page_no}|{line["y"]:.2f}|{name}'.encode()).hexdigest()[:20]
                last={'record_id':rid,'source_sha256':sha,'source_page':page_no,
                      'source_y':round(line['y'],2),**ctx,'date_provenance':('EXPLICIT_ROW_CONTEXT' if ctx['game_date'] else 'UNRESOLVED'),'player':name,
                      'status':sm.group(0).upper(),'reason':reason_text,
                      'parse_status':'','flags':'','eligible_for_asof_training':False,
                      '_last_y':line['y']}
                rows.append(last);page_rows.append(last)
            elif reason_text and not nm and not sm:
                if (last is not None and not d and not m and not matches and
                    not PLAYER.search(txt) and 0 < line['y']-last['_last_y']<=18):
                    last['reason']=(last['reason']+' '+reason_text).strip()
                    last['_last_y']=line['y']
                    diagnostics['continuation_lines']+=1
                else:
                    diagnostics['orphan_continuations']+=1
                    last=None
            elif sm or nm or d or m or matches:
                # Do not attach a later reason to an unrelated preceding player.
                if not (sm and nm):last=None
        for r in page_rows:
            flags=[]
            for k in ('game_date','matchup','team'):
                if not r[k]:flags.append(k.upper()+'_UNRESOLVED')
            if not r['reason']:flags.append('REASON_UNRESOLVED')
            if mode=='REUSED_COLUMNS':flags.append('INHERITED_COLUMN_LAYOUT_UNVERIFIED')
            r['flags']='|'.join(flags)
            r['parse_status']='REVIEW_REQUIRED' if flags else 'AUTO_CANDIDATE'
            r.pop('_last_y',None)
        diagnostics['per_page'].append({'page':page_no,'mode':mode,
            'records':len(page_rows),
            'complete':sum(r['parse_status']=='AUTO_CANDIDATE' for r in page_rows),
            'review_required':sum(r['parse_status']=='REVIEW_REQUIRED' for r in page_rows)})
    # Document-scoped date inference is deliberately conservative: one unique
    # explicit date, plus an explicit matchup on the target row. No team or
    # player identity is inferred across page boundaries.
    explicit_dates=sorted({r['game_date'] for r in rows if r['game_date']})
    diagnostics['document_dates']=explicit_dates
    diagnostics['date_conflicts']=len(explicit_dates)>1
    if len(explicit_dates)==1:
        for r in rows:
            if not r['game_date'] and r['matchup']:
                r['game_date']=explicit_dates[0]
                r['date_provenance']='DOCUMENT_UNIQUE_DATE_INFERRED'
                diagnostics['date_backfills']+=1
                flags=[x for x in r['flags'].split('|') if x and x!='GAME_DATE_UNRESOLVED']
                flags.append('DATE_INFERRED_REVIEW_REQUIRED')
                r['flags']='|'.join(flags)
                r['parse_status']='REVIEW_REQUIRED'
    # Recalculate counts after conservative backfill, without counting inferred
    # fields as independently verified.
    for page in diagnostics['per_page']:
        group=[r for r in rows if r['source_page']==page['page']]
        page['date_inferred']=sum(r['date_provenance']=='DOCUMENT_UNIQUE_DATE_INFERRED' for r in group)
        page['complete']=sum(r['parse_status']=='AUTO_CANDIDATE' for r in group)
        page['review_required']=sum(r['parse_status']=='REVIEW_REQUIRED' for r in group)
    return rows,diagnostics

def process_pdf(pdf_path, source_url, output_dir):
    from .injury_asof import parse_official_url,verify_pdf_bytes
    from .injury_auto import process_pdf as old_process
    import pymupdf
    parse_official_url(source_url)
    raw=Path(pdf_path).read_bytes();sha=verify_pdf_bytes(raw)
    with pymupdf.open(stream=raw,filetype='pdf') as doc:
        pages=[{'page':i+1,'words':page.get_text('words'),'width':page.rect.width} for i,page in enumerate(doc)]
    rows,diag=parse_word_pages(pages,sha)
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    out_csv=out/(sha+'.s7_7_layout_candidates.csv')
    with out_csv.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    # Run legacy parser in separate directory; preserve its results for comparison.
    baseline=old_process(pdf_path,source_url,out/'s7_4_comparison')
    report={'status':'RESEARCH_ONLY','source_sha256':sha,'total_layout_records':len(rows),
        'layout_complete_records':sum(r['parse_status']=='AUTO_CANDIDATE' for r in rows),
        'layout_review_required':sum(r['parse_status']=='REVIEW_REQUIRED' for r in rows),
        'rows_with_date':sum(bool(r['game_date']) for r in rows),
        'date_inferred_rows':diag['date_backfills'],
        's7_4_status_lines':baseline['total_status_lines'],'s7_4_auto_candidates':baseline['auto_candidates'],
        's7_4_review_required':baseline['review_required'],
        'diagnostics':diag,'output_csv':str(out_csv),'historical_publication_verified':False,
        'eligible_for_asof_training':False,
        'limitations':['Counts are not accuracy metrics','Column positions may be reused but team/matchup context is never inherited across pages',
            'Wrapped reasons are heuristic and must be spot-checked','Inferred document date requires review and does not prove as-of availability','No as-of publication verification']}
    (out/(sha+'.s7_7_layout_manifest.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report
