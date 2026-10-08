"""S7.9 evidence-only context proposals and orphan trace for official NBA PDF.

Does not modify source records or assert publication time / training eligibility.
"""
from __future__ import annotations
import csv, json, re
from pathlib import Path
from .injury_auto import DATE, MATCHUP, TEAMS, PLAYER, STATUS
from .injury_layout import word_lines, infer_columns, cells

PROPOSAL_FIELDS=('source_page','source_y','player','status','missing_fields','candidate_game_date','candidate_matchup','candidate_team','evidence_page','evidence_y','evidence_text','evidence_rule','decision')
TRACE_FIELDS=('source_page','source_y','text','reason_cell','classification','preceding_player','gap_points')

def explicit_context(line):
    text=' '.join(str(w[4]) for w in line['words'])
    d=DATE.search(text)
    date=''
    if d:
        mm,dd,yyyy=d.group(1).split('/')
        date=f'{yyyy}-{mm}-{dd}'
    m=MATCHUP.search(text)
    teams=[t for t in TEAMS if re.search(r'(?<!\w)'+re.escape(t)+r'(?!\w)',text)]
    return {'game_date':date,'matchup':m.group(0) if m else '',
            'team':teams[0] if len(teams)==1 else '', 'text':text}

def collect_evidence(pages):
    """Capture explicit source context and reason-only orphan candidates."""
    evidence=[]; traces=[]; previous_columns=None;previous_width=None
    for p in pages:
        page=p['page']; width=p.get('width');lines=word_lines(p['words'])
        own=infer_columns(lines)
        if own: previous_columns=own;previous_width=width
        compatible=(width is not None and previous_width is not None and
                    abs(float(width)-float(previous_width))<=2)
        columns=own or (previous_columns if compatible else None)
        last_player='';last_y=None
        for line in lines:
            ctx=explicit_context(line); y=round(line['y'],2)
            if any(ctx[k] for k in ('game_date','matchup','team')):
                evidence.append({'page':page,'y':y,**ctx})
            if not columns:continue
            c=cells(line,columns)
            pt=c.get('player','');st=c.get('status','');reason=c.get('reason','')
            if PLAYER.search(pt) and STATUS.search(st):
                last_player=pt;last_y=y
            elif reason and not PLAYER.search(pt) and not STATUS.search(st):
                gap=round(y-last_y,2) if last_y is not None else None
                # A trace is not necessarily a true orphan; we do not attach text.
                classification=('NEAR_PLAYER_UNATTACHED' if gap is not None and 0<gap<=18
                                else 'NO_SAFE_PLAYER_ANCHOR')
                traces.append({'source_page':page,'source_y':y,'text':ctx['text'],
                    'reason_cell':reason,'classification':classification,
                    'preceding_player':last_player,'gap_points':gap if gap is not None else ''})
                if classification=='NO_SAFE_PLAYER_ANCHOR':last_player='';last_y=None
    return evidence,traces

def propose(rows,evidence):
    """Return suggestions, never verified assignments; require page-local evidence."""
    proposals=[]
    for row in rows:
        missing=[k for k in ('game_date','matchup','team') if not row.get(k)]
        if not missing:continue
        try:page=int(row['source_page']);y=float(row['source_y'])
        except (KeyError,ValueError,TypeError):continue
        earlier=[e for e in evidence if e['page']==page and e['y']<=y]
        # For each missing field, use the most recent explicit value on the same page.
        candidates={};sources={}
        for field in missing:
            found=next((e for e in reversed(earlier) if e[field]),None)
            if found:candidates[field]=found[field];sources[field]=found
        if not candidates:
            proposals.append({'source_page':page,'source_y':y,'player':row.get('player',''),
                'status':row.get('status',''),'missing_fields':'|'.join(missing),
                'candidate_game_date':'','candidate_matchup':'','candidate_team':'',
                'evidence_page':'','evidence_y':'','evidence_text':'',
                'evidence_rule':'NO_PAGE_LOCAL_EXPLICIT_EVIDENCE','decision':'UNRESOLVED'})
            continue
        # Multiple anchors for different fields are documented as a range, not conflated.
        anchors=list({(e['page'],e['y'],e['text']) for e in sources.values()})
        proposals.append({'source_page':page,'source_y':y,'player':row.get('player',''),
            'status':row.get('status',''),'missing_fields':'|'.join(missing),
            'candidate_game_date':candidates.get('game_date',''),
            'candidate_matchup':candidates.get('matchup',''),
            'candidate_team':candidates.get('team',''),
            'evidence_page':page,'evidence_y':'|'.join(str(a[1]) for a in sorted(anchors)),
            'evidence_text':' || '.join(a[2] for a in sorted(anchors)),
            'evidence_rule':'PAGE_LOCAL_PRECEDING_EXPLICIT_CONTEXT',
            'decision':'REVIEW_PROPOSAL_NOT_APPLIED'})
    return proposals

def read_rows(path):
    with Path(path).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def audit_pdf(pdf_path,source_url,s77_csv,output_dir):
    from .injury_asof import parse_official_url,verify_pdf_bytes
    import pymupdf
    parse_official_url(source_url)
    raw=Path(pdf_path).read_bytes();sha=verify_pdf_bytes(raw)
    rows=read_rows(s77_csv)
    if any(r.get('source_sha256')!=sha for r in rows):
        raise ValueError('S7.7 CSV source hash does not match PDF')
    with pymupdf.open(stream=raw,filetype='pdf') as doc:
        pages=[{'page':i+1,'width':p.rect.width,'words':p.get_text('words')}
               for i,p in enumerate(doc)]
    evidence,traces=collect_evidence(pages)
    proposals=propose(rows,evidence)
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    pp=out/(sha+'.s7_9_context_proposals.csv')
    tp=out/(sha+'.s7_9_reason_line_trace.csv')
    for path,fields,data in ((pp,PROPOSAL_FIELDS,proposals),(tp,TRACE_FIELDS,traces)):
        with path.open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(data)
    report={'status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','source_sha256':sha,
        's7_7_records':len(rows),'s7_7_missing_context_records':sum(
            any(not r.get(k) for k in ('game_date','matchup','team')) for r in rows),
        'context_proposals':sum(p['decision']=='REVIEW_PROPOSAL_NOT_APPLIED' for p in proposals),
        'unresolved_context':sum(p['decision']=='UNRESOLVED' for p in proposals),
        'reason_line_traces':len(traces),'trace_classifications':{
            k:sum(t['classification']==k for t in traces)
            for k in ('NEAR_PLAYER_UNATTACHED','NO_SAFE_PLAYER_ANCHOR')},
        'context_proposals_csv':str(pp),'reason_line_trace_csv':str(tp),
        'original_records_modified':0,'historical_publication_verified':False,
        'eligible_for_asof_training':False,
        'limitations':['Context proposals are NOT automatically applied',
            'Page-local proximity is not independent accuracy verification',
            'Trace lines are candidates, not proven orphans',
            'No cross-page team/matchup inheritance',
            'Publication timestamp remains unverified']}
    jp=out/(sha+'.s7_9_audit.json');jp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    return report
