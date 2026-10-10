"""S8.22.10.3: fail-closed cross-page candidate attribution for archived injury PDFs.

Never certifies source publication time, player identity, availability or training.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import sys
import uuid
from pathlib import Path
from pypdf import PdfReader

SLATE = {'DAL@WAS', 'NYK@ATL', 'BOS@PHI', 'MIL@TOR', 'ORL@CHI', 'MIN@PHX', 'SAC@LAL', 'CLE@POR'}
TEAMS = {
 'Dallas Mavericks':'DAL','Washington Wizards':'WAS','New York Knicks':'NYK','Atlanta Hawks':'ATL',
 'Boston Celtics':'BOS','Philadelphia 76ers':'PHI','Milwaukee Bucks':'MIL','Toronto Raptors':'TOR',
 'Orlando Magic':'ORL','Chicago Bulls':'CHI','Minnesota Timberwolves':'MIN','Phoenix Suns':'PHX',
 'Sacramento Kings':'SAC','Los Angeles Lakers':'LAL','Cleveland Cavaliers':'CLE','Portland Trail Blazers':'POR',
 'Miami Heat':'MIA','Oklahoma City Thunder':'OKC','Golden State Warriors':'GSW',
 'Brooklyn Nets':'BKN','Charlotte Hornets':'CHA','Detroit Pistons':'DET','Houston Rockets':'HOU',
 'Indiana Pacers':'IND','Memphis Grizzlies':'MEM','New Orleans Pelicans':'NOP','San Antonio Spurs':'SAS',
 'Utah Jazz':'UTA','Denver Nuggets':'DEN','Los Angeles Clippers':'LAC'
}
STATUSES={'Out','Questionable','Doubtful','Probable','Available'}
FIELDS_PLAYER=['page','y','matchup_candidate','team_candidate','team_name_candidate','player_name_candidate','status_candidate','reason_candidate','reason_y_positions','context_origin','slate_scope','review_status','player_verified','historical_asof_certified']
FIELDS_SUB=['page','y','matchup_candidate','team_candidate','team_name_candidate','submission_text','context_origin','slate_scope','review_status']
FIELDS_AMBIG=['page','y','issue','detail']


def fragments(page):
    result=[]
    def visit(text,cm,tm,font_dict,font_size):
        value=' '.join(text.split())
        if value:
            x,y=float(tm[4]),float(tm[5])
            if 0<=x<=1100 and 0<=y<=2000:
                result.append({'x':x,'y':y,'text':value})
    page.extract_text(visitor_text=visit)
    return result


def column(x):
    if x<100:return 'date'
    if x<195:return 'time'
    if x<260:return 'matchup'
    if x<420:return 'team'
    if x<580:return 'player'
    if x<660:return 'status'
    return 'reason'


def group_lines(items,tolerance=2.0):
    groups=[]
    for f in sorted(items,key=lambda z:(z['y'],z['x'])):
        if not groups or abs(groups[-1][0]['y']-f['y'])>tolerance:groups.append([f])
        else:groups[-1].append(f)
    return [{'y':sum(f['y'] for f in g)/len(g),
             'cells':{c:' '.join(f['text'] for f in sorted(g,key=lambda z:z['x']) if column(f['x'])==c)
                      for c in ['date','time','matchup','team','player','status','reason']}} for g in groups]


def matchup(text):
    text=text.strip().upper()
    return text if re.fullmatch(r'[A-Z]{2,3}@[A-Z]{2,3}',text) else None


def scope(game):
    if not game:return 'UNRESOLVED'
    return 'IN_VALIDATED_EIGHT_GAME_SLATE' if game in SLATE else 'OUTSIDE_VALIDATED_EIGHT_GAME_SLATE'


def parse_pages(pages):
    players=[]; submissions=[]; ambiguities=[]
    game=None; team=None; team_name=None; last_page=None; context_page=None
    for page_no,items in enumerate(pages,1):
        # Layout observed on source: headers above y=120, footers at y=545.4.
        # Reject those regions before attempting player/status attribution.
        lines=[l for l in group_lines(items) if 120<=l['y']<525]
        anchors=[]
        for line in lines:
            c=line['cells']; st=c['status'].strip(); reason=c['reason'].strip()
            if st in STATUSES and c['player'].strip():anchors.append(('player',line))
            elif re.search(r'\bNOT\s+YET\s+SUBMITTED\b',reason,re.I):anchors.append(('submission',line))
            elif st or c['player'].strip():
                ambiguities.append({'page':page_no,'y':round(line['y'],1),'issue':'UNMATCHED_PLAYER_OR_STATUS','detail':str({'player':c['player'],'status':st})})
        # Walk document in page and y order, never back-search only within a page.
        # Explicit team heading replaces inherited team. Explicit matchup resets team.
        # When new team appears without matchup, only inherit if the team belongs to the current game.
        events=sorted([(l['y'],0,'header',l) for l in lines if matchup(l['cells']['matchup']) or l['cells']['team'] in TEAMS]
                      +[(l['y'],1,kind,l) for kind,l in anchors],key=lambda e:(e[0],e[1]))
        for y,_,kind,line in events:
            c=line['cells']
            if kind=='header':
                new_game=matchup(c['matchup'])
                if new_game:
                    game=new_game; team=None;team_name=None
                new_name=c['team'].strip()
                if new_name in TEAMS:
                    new_team=TEAMS[new_name]
                    if game and new_team not in game.split('@'):
                        ambiguities.append({'page':page_no,'y':round(y,1),'issue':'TEAM_MATCHUP_CONFLICT','detail':f'{new_name} / {game}'})
                        game=None
                    team=new_team;team_name=new_name
                    context_page=page_no
                continue
            origin='CROSS_PAGE_CONTINUATION' if context_page is not None and context_page<page_no else 'SAME_PAGE_OR_PRIOR_CONTEXT'
            # Context must match explicit matchup participants; never claim attribution otherwise.
            if game and team and team not in game.split('@'):
                ambiguities.append({'page':page_no,'y':round(y,1),'issue':'TEAM_MATCHUP_CONFLICT','detail':f'{team} / {game}'})
                game=None
            if not game or not team:
                ambiguities.append({'page':page_no,'y':round(y,1),'issue':'MISSING_CONTEXT','detail':f'game={game} team={team_name}'})
            if kind=='submission':
                submissions.append({'page':page_no,'y':round(y,1),'matchup_candidate':game or '',
                    'team_candidate':team or '', 'team_name_candidate':team_name or '',
                    'submission_text':c['reason'],'context_origin':origin,'slate_scope':scope(game),
                    'review_status':'MANUAL_REVIEW_REQUIRED'})
            else:
                # Reason text can appear 7pt above/below player anchor; delimit by adjacent anchors.
                pos=next(i for i,(_,anchor) in enumerate(anchors) if anchor is line)
                prev_y=anchors[pos-1][1]['y'] if pos else y-24
                next_y=anchors[pos+1][1]['y'] if pos+1<len(anchors) else y+24
                lo=max(y-15,(prev_y+y)/2); hi=min(y+15,(next_y+y)/2)
                reason_lines=[l for l in lines if lo-.2<=l['y']<=hi+.2 and l['cells']['reason']
                              and not re.search(r'NOT\s+YET\s+SUBMITTED',l['cells']['reason'],re.I)]
                reason=' '.join(l['cells']['reason'] for l in reason_lines)
                if not reason:
                    ambiguities.append({'page':page_no,'y':round(y,1),'issue':'REASON_MISSING','detail':c['player']})
                players.append({'page':page_no,'y':round(y,1),'matchup_candidate':game or '',
                    'team_candidate':team or '', 'team_name_candidate':team_name or '',
                    'player_name_candidate':c['player'],'status_candidate':c['status'],
                    'reason_candidate':reason,'reason_y_positions':'|'.join(str(round(l['y'],1)) for l in reason_lines),
                    'context_origin':origin,'slate_scope':scope(game),
                    'review_status':'MANUAL_REVIEW_REQUIRED','player_verified':False,'historical_asof_certified':False})
            last_page=page_no
    return players,submissions,ambiguities


def write_csv(path,rows,fields):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def run(root,receipt_path):
    root=root.resolve(); receipt_path=receipt_path.resolve()
    if not receipt_path.is_file() or not receipt_path.is_relative_to(root):raise ValueError('Receipt must be within project')
    receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
    if receipt.get('milestone')!='S8.22.10' or receipt.get('decision')!='BLOCK_TRAINING':raise ValueError('Unexpected evidence receipt')
    source=(root/receipt['source_file']).resolve()
    if not source.is_relative_to(root) or source.parent!=receipt_path.parent or not source.is_file():raise ValueError('Source location mismatch')
    data=source.read_bytes()
    if not data.startswith(b'%PDF-') or hashlib.sha256(data).hexdigest()!=receipt['sha256']:raise ValueError('Source PDF SHA mismatch')
    reader=PdfReader(io.BytesIO(data))
    if reader.is_encrypted:raise ValueError('Encrypted PDF')
    players,subs,ambiguities=parse_pages([fragments(page) for page in reader.pages])
    out=root/'research/p0_s8/s8_22_10_3/results/2023-11-15'/uuid.uuid4().hex
    out.mkdir(parents=True,exist_ok=False)
    write_csv(out/'player_status_candidates.csv',players,FIELDS_PLAYER)
    write_csv(out/'team_submission_candidates.csv',subs,FIELDS_SUB)
    write_csv(out/'ambiguities.csv',ambiguities,FIELDS_AMBIG)
    out_scope=[{'record_type':typ,**row} for typ,rows in [('PLAYER',players),('TEAM_SUBMISSION',subs)] for row in rows if row['slate_scope']=='OUTSIDE_VALIDATED_EIGHT_GAME_SLATE']
    # Separate minimal, stable out-of-slate audit schema.
    write_csv(out/'out_of_slate_candidates.csv',[
        {'record_type':r['record_type'],'page':r['page'],'matchup_candidate':r['matchup_candidate'],
         'team_candidate':r['team_candidate'],'name_or_notice':r.get('player_name_candidate',r.get('submission_text',''))}
        for r in out_scope],['record_type','page','matchup_candidate','team_candidate','name_or_notice'])
    counts={'player_candidates':len(players),'team_submission_candidates':len(subs),'ambiguities':len(ambiguities),
            'cross_page_player_candidates':sum(r['context_origin']=='CROSS_PAGE_CONTINUATION' for r in players),
            'out_of_slate_candidates':len(out_scope),
            'unresolved_context_candidates':sum(r['slate_scope']=='UNRESOLVED' for r in players+subs)}
    report={'milestone':'S8.22.10.3','pdf_sha256':receipt['sha256'],'pages':len(reader.pages),**counts,
            'manual_table_review':'REQUIRED','historical_asof':'NOT_CERTIFIED','decision':'BLOCK_TRAINING',
            'note':'PDF table candidate reconstruction only; no source publication, player identity, eligibility, DNP, or training certification.'}
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',out/'review.json')
    for k,v in counts.items():print(k.upper().replace('_',' ')+':',v)
    print('HISTORICAL AS-OF: NOT_CERTIFIED\nDECISION: BLOCK_TRAINING')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project-root',default='.');p.add_argument('--receipt',required=True)
    a=p.parse_args()
    try:run(Path(a.project_root),Path(a.receipt))
    except Exception as e:print('FAIL CLOSED:',e,file=sys.stderr);sys.exit(2)
if __name__=='__main__':main()
