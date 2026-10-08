"""S7.11 stateful table reconstruction. Research-only, never as-of eligible.

Uses PDF word coordinates, explicit section cells and document-order inheritance.
Never uses player roster knowledge to infer teams. Original S7.7 rows unchanged.
"""
from __future__ import annotations
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from .injury_layout import word_lines
from .injury_auto import TEAMS, PLAYER, STATUS, MATCHUP, DATE

FIELDS = ('record_id','source_sha256','source_page','source_y','game_date','matchup','team','player','status','reason','date_provenance','matchup_provenance','team_provenance','flags','parse_status','eligible_for_asof_training')
COMPARE_FIELDS = ('source_page','player','status','old_game_date','new_game_date','old_matchup','new_matchup','old_team','new_team','changed_fields','new_flags')


def _cells(line, width=841.95):
    """Column lanes scaled to report width; word left edge avoids crossing lanes."""
    scale=float(width)/841.95
    lanes=(115*scale,195*scale,260*scale,420*scale,580*scale,665*scale)
    keys=('date','time','matchup','team','player','status','reason')
    out={k:[] for k in keys}
    for w in line['words']:
        x=float(w[0]); idx=sum(x>=b for b in lanes)
        out[keys[idx]].append(str(w[4]))
    return {k:' '.join(v).strip() for k,v in out.items()}


def _date(text):
    m=DATE.search(text)
    if not m:return ''
    mm,dd,yyyy=m.group(1).split('/')
    return f'{yyyy}-{mm}-{dd}'


def _team(text):
    matches=[t for t in TEAMS if t.lower()==text.strip().lower()]
    return matches[0] if len(matches)==1 else ''


def parse_pages(pages, sha):
    state={'game_date':'','matchup':'','team':''}
    provenance={'game_date':'','matchup':'','team':''}
    rows=[]; events=[]; skipped_submissions=0; previous_width=None
    for p in pages:
        page=int(p['page']); width=float(p.get('width',841.95))
        if previous_width is not None and abs(width-previous_width)>2:
            state={'game_date':'','matchup':'','team':''}
            provenance={'game_date':'','matchup':'','team':''}
            events.append({'page':page,'y':'','type':'LAYOUT_CHANGE_RESET','value':''})
        previous_width=width
        for line in word_lines(p['words']):
            c=_cells(line,width); y=round(float(line['y']),2)
            if 'player name' in c['player'].lower() or 'current status' in c['status'].lower():continue
            d=_date(c['date'])
            m=MATCHUP.fullmatch(c['matchup'])
            t=_team(c['team'])
            if d:
                state['game_date']=d; provenance['game_date']=f'EXPLICIT:p{page}:y{y}'
                # A new dated game must not carry an earlier game assignment.
                state['matchup']='';state['team']=''
                provenance['matchup']='';provenance['team']=''
                events.append({'page':page,'y':y,'type':'DATE','value':d})
            if m:
                state['matchup']=m.group(0);state['team']=''
                provenance['matchup']=f'EXPLICIT:p{page}:y{y}';provenance['team']=''
                events.append({'page':page,'y':y,'type':'MATCHUP','value':m.group(0)})
            if t:
                state['team']=t;provenance['team']=f'EXPLICIT:p{page}:y{y}'
                events.append({'page':page,'y':y,'type':'TEAM','value':t})
            # A team without a known game is unresolved, not a guessed game.
            if 'NOT YET SUBMITTED' in c['reason'].upper():
                skipped_submissions+=1
                events.append({'page':page,'y':y,'type':'NOT_YET_SUBMITTED','value':state['team']})
                continue
            nm=PLAYER.fullmatch(c['player'])
            sm=STATUS.fullmatch(c['status'])
            if not (nm and sm):continue
            name=nm.group(2)+' '+nm.group(1)
            rid=hashlib.sha256(f'{sha}|{page}|{y:.2f}|{name}'.encode()).hexdigest()[:20]
            flags=['STRUCTURAL_CONTEXT_REVIEW_REQUIRED']
            for field in ('game_date','matchup','team'):
                if not state[field]:flags.append(field.upper()+'_UNRESOLVED')
            if not c['reason']:flags.append('REASON_UNRESOLVED')
            rows.append({'record_id':rid,'source_sha256':sha,'source_page':page,'source_y':y,
                **state,'player':name,'status':sm.group(0).upper(),'reason':c['reason'],
                'date_provenance':provenance['game_date'],'matchup_provenance':provenance['matchup'],
                'team_provenance':provenance['team'],'flags':'|'.join(flags),
                'parse_status':'REVIEW_REQUIRED','eligible_for_asof_training':False})
    return rows,{'events':events,'not_yet_submitted_sections':skipped_submissions}


def compare(old,new):
    # Match only unique page/player/status identities; duplicates remain unresolved.
    lookup={};counts=Counter((str(r['source_page']),r['player'],r['status']) for r in old)
    for r in old:
        key=(str(r['source_page']),r['player'],r['status'])
        if counts[key]==1:lookup[key]=r
    changes=[];matched=0;recovered=Counter();conflicts=Counter()
    for r in new:
        oldrow=lookup.get((str(r['source_page']),r['player'],r['status']))
        if not oldrow:continue
        matched+=1; changed=[]
        for field in ('game_date','matchup','team'):
            before=oldrow.get(field,'');after=r[field]
            if before!=after:
                changed.append(field)
                if not before and after:recovered[field]+=1
                elif before and after:conflicts[field]+=1
        if changed:
            changes.append({'source_page':r['source_page'],'player':r['player'],'status':r['status'],
                **{'old_'+k:oldrow.get(k,'') for k in ('game_date','matchup','team')},
                **{'new_'+k:r[k] for k in ('game_date','matchup','team')},
                'changed_fields':'|'.join(changed),'new_flags':r['flags']})
    return changes,{'matched_rows':matched,'unmatched_new_rows':len(new)-matched,
                    'recovered_fields':dict(recovered),'conflicting_nonempty_fields':dict(conflicts)}


def _write(path,fields,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)


def run(pdf_path,s77_csv,output_dir):
    import pymupdf
    raw=Path(pdf_path).read_bytes()
    if not raw.startswith(b'%PDF-'):raise ValueError('PDF header missing')
    sha=hashlib.sha256(raw).hexdigest()
    with Path(s77_csv).open(newline='',encoding='utf-8-sig') as f:old=list(csv.DictReader(f))
    if not old or any(r.get('source_sha256')!=sha for r in old):
        raise ValueError('S7.7 source SHA256 does not match PDF')
    with pymupdf.open(stream=raw,filetype='pdf') as doc:
        pages=[{'page':i+1,'width':p.rect.width,'words':p.get_text('words')} for i,p in enumerate(doc)]
    rows,diag=parse_pages(pages,sha)
    changes,comparison=compare(old,rows)
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    cp=out/f'{sha}.s7_11_candidates.csv';dp=out/f'{sha}.s7_11_differences.csv'
    ep=out/f'{sha}.s7_11_section_events.csv'
    _write(cp,FIELDS,rows);_write(dp,COMPARE_FIELDS,changes)
    _write(ep,('page','y','type','value'),diag['events'])
    report={'status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','source_sha256':sha,
        's7_7_records':len(old),'s7_11_records':len(rows),'comparison':comparison,
        's7_11_missing_context':sum(any(not r[k] for k in ('game_date','matchup','team')) for r in rows),
        'section_events':dict(Counter(e['type'] for e in diag['events'])),
        'not_yet_submitted_sections':diag['not_yet_submitted_sections'],
        'original_records_modified':0,'historical_publication_verified':False,
        'eligible_for_asof_training':False,'candidates_csv':str(cp),'differences_csv':str(dp),
        'section_events_csv':str(ep),
        'limitations':['Fixed report column lanes require verification against PDF geometry',
            'Cross-page inherited context is a structural hypothesis requiring spot checks',
            'No independent ground truth or historical publication-time proof',
            'All candidates remain REVIEW_REQUIRED and training ineligible']}
    jp=out/f'{sha}.s7_11_report.json';jp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report
