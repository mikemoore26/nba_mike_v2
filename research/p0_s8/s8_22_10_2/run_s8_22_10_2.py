"""Fail-closed coordinate-based candidate reconstruction of a historical NBA injury PDF.

No output is certified player identity, historical as-of, DNP, or training eligibility.
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

GAMES = {'DAL@WAS': ('DAL','WAS'), 'NYK@ATL': ('NYK','ATL'), 'BOS@PHI': ('BOS','PHI'), 'MIL@TOR': ('MIL','TOR'), 'ORL@CHI': ('ORL','CHI'), 'MIN@PHX': ('MIN','PHX'), 'SAC@LAL': ('SAC','LAL'), 'CLE@POR': ('CLE','POR')}
TEAM_NAMES = {'Dallas Mavericks':'DAL','Washington Wizards':'WAS','New York Knicks':'NYK','Atlanta Hawks':'ATL','Boston Celtics':'BOS','Philadelphia 76ers':'PHI','Milwaukee Bucks':'MIL','Toronto Raptors':'TOR','Orlando Magic':'ORL','Chicago Bulls':'CHI','Minnesota Timberwolves':'MIN','Phoenix Suns':'PHX','Sacramento Kings':'SAC','Los Angeles Lakers':'LAL','Cleveland Cavaliers':'CLE','Portland Trail Blazers':'POR'}
STATUSES = {'Out','Questionable','Doubtful','Probable','Available'}
COLS = [(0,100,'date'),(100,195,'time'),(195,260,'matchup'),(260,420,'team'),(420,580,'player'),(580,660,'status'),(660,1000,'reason')]


def fragments(page):
    """Use source PDF text matrix (as demonstrated by the source diagnostic)."""
    out=[]
    def visitor(text, cm, tm, font_dict, font_size):
        s=' '.join(text.split())
        if s:
            x,y=float(tm[4]),float(tm[5])
            if 0 <= x <= 1100 and 0 <= y <= 2000:
                out.append({'x':x,'y':y,'text':s})
    page.extract_text(visitor_text=visitor)
    return out


def column(x):
    return next((name for low,high,name in COLS if low <= x < high), None)


def group_lines(frags, tolerance=2.0):
    groups=[]
    for f in sorted(frags,key=lambda z:(z['y'],z['x'])):
        if not groups or abs(groups[-1][0]['y']-f['y'])>tolerance:
            groups.append([f])
        else:groups[-1].append(f)
    return [{'y':sum(f['y'] for f in g)/len(g),'cells':{col:' '.join(f['text'] for f in sorted(g,key=lambda z:z['x']) if column(f['x'])==col) for _,_,col in COLS}} for g in groups]


def parse_pages(pages):
    players=[]; submissions=[]; ambiguities=[]
    game=None;team=None; team_name=None
    for page_number,frags in enumerate(pages,1):
        lines=[line for line in group_lines(frags) if line['y']>120]
        # Status cells provide player-row anchors. Team submission notices anchor on their own line.
        anchors=[]
        for line in lines:
            c=line['cells']; status=c['status'].strip(); reason=c['reason'].strip()
            if status in STATUSES and c['player'].strip():
                anchors.append(('player',line))
            elif re.search(r'NOT\s+YET\s+SUBMITTED',reason,re.I):
                anchors.append(('submission',line))
            elif status or c['player'].strip():
                ambiguities.append({'page':page_number,'y':round(line['y'],1),'issue':'UNMATCHED_PLAYER_OR_STATUS','detail':str({'player':c['player'],'status':status})})
        for index,(kind,anchor) in enumerate(anchors):
            y=anchor['y']; c=anchor['cells']
            # Explicit matchup/team headers may precede anchor and remain valid until next header.
            # Search only current page. Never silently inherit context from a previous page.
            preceding=[l for l in lines if l['y']<=y+2]
            game_headers=[l for l in preceding if l['cells']['matchup'] in GAMES]
            if game_headers: game=game_headers[-1]['cells']['matchup']
            else: game=None
            team_headers=[l for l in preceding if l['cells']['team'] in TEAM_NAMES]
            if team_headers: team_name=team_headers[-1]['cells']['team'];team=TEAM_NAMES[team_name]
            else: team_name=None;team=None
            if game and team and team not in GAMES[game]:
                ambiguities.append({'page':page_number,'y':round(y,1),'issue':'TEAM_GAME_CONFLICT','detail':f'{team} / {game}'})
                team=None
            if not game or not team:
                ambiguities.append({'page':page_number,'y':round(y,1),'issue':'MISSING_PAGE_CONTEXT','detail':f'game={game} team={team_name}'})
            if kind=='submission':
                submissions.append({'page':page_number,'y':round(y,1),'matchup_candidate':game or '', 'team_candidate':team or '', 'team_name_candidate':team_name or '', 'submission_text':c['reason'], 'review_status':'MANUAL_REVIEW_REQUIRED'})
                continue
            # Reason fragments between midpoint of preceding and next player/submission anchors;
            # status row may have vertically centered multi-line reason. Tight cap avoids borrowing from neighboring blocks.
            previous_y=anchors[index-1][1]['y'] if index else y-24
            next_y=anchors[index+1][1]['y'] if index+1<len(anchors) else y+24
            lower=max(y-15,(previous_y+y)/2)
            upper=min(y+15,(next_y+y)/2)
            reason_lines=[l for l in lines if lower-0.2<=l['y']<=upper+0.2 and l['cells']['reason'] and 'NOT YET SUBMITTED' not in l['cells']['reason'].upper()]
            reason=' '.join(l['cells']['reason'] for l in reason_lines)
            if not reason:
                ambiguities.append({'page':page_number,'y':round(y,1),'issue':'REASON_MISSING','detail':c['player']})
            players.append({'page':page_number,'y':round(y,1),'matchup_candidate':game or '', 'team_candidate':team or '', 'team_name_candidate':team_name or '', 'player_name_candidate':c['player'], 'status_candidate':c['status'], 'reason_candidate':reason, 'reason_y_positions':'|'.join(str(round(l['y'],1)) for l in reason_lines), 'review_status':'MANUAL_REVIEW_REQUIRED','player_verified':False,'historical_asof_certified':False})
    return players,submissions,ambiguities


def write_csv(path, rows, fields):
    with path.open('w',encoding='utf-8',newline='') as fh:
        writer=csv.DictWriter(fh,fieldnames=fields);writer.writeheader();writer.writerows(rows)


def run(root, receipt_path):
    root=root.resolve();receipt_path=receipt_path.resolve()
    receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
    if receipt.get('milestone')!='S8.22.10' or receipt.get('decision')!='BLOCK_TRAINING':raise ValueError('Unexpected evidence receipt')
    source=(root/receipt['source_file']).resolve()
    if not source.is_relative_to(root) or source.parent!=receipt_path.parent or not source.is_file():raise ValueError('Source location mismatch')
    data=source.read_bytes()
    if not data.startswith(b'%PDF-') or hashlib.sha256(data).hexdigest()!=receipt['sha256']:raise ValueError('Source PDF SHA mismatch')
    reader=PdfReader(io.BytesIO(data))
    if reader.is_encrypted:raise ValueError('Encrypted source PDF')
    players,submissions,ambiguities=parse_pages([fragments(p) for p in reader.pages])
    out=root/'research/p0_s8/s8_22_10_2/results/2023-11-15'/uuid.uuid4().hex
    out.mkdir(parents=True,exist_ok=False)
    write_csv(out/'player_status_candidates.csv',players,['page','y','matchup_candidate','team_candidate','team_name_candidate','player_name_candidate','status_candidate','reason_candidate','reason_y_positions','review_status','player_verified','historical_asof_certified'])
    write_csv(out/'team_submission_candidates.csv',submissions,['page','y','matchup_candidate','team_candidate','team_name_candidate','submission_text','review_status'])
    write_csv(out/'ambiguities.csv',ambiguities,['page','y','issue','detail'])
    report={'milestone':'S8.22.10.2','pdf_sha256':receipt['sha256'],'pages':len(reader.pages),'player_candidates':len(players),'team_submission_candidates':len(submissions),'ambiguities':len(ambiguities),'manual_table_review':'REQUIRED','historical_asof':'NOT_CERTIFIED','decision':'BLOCK_TRAINING','note':'Layout candidates only; no verified player identity, availability, publication time or training permission.'}
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',out/'review.json')
    print('PLAYER CANDIDATES:',len(players));print('TEAM SUBMISSION CANDIDATES:',len(submissions));print('AMBIGUITIES:',len(ambiguities));print('HISTORICAL AS-OF: NOT_CERTIFIED');print('DECISION: BLOCK_TRAINING')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project-root',default='.');p.add_argument('--receipt',required=True)
    args=p.parse_args()
    try:run(Path(args.project_root),Path(args.receipt))
    except Exception as e:print('FAIL CLOSED:',e,file=sys.stderr);sys.exit(2)
if __name__=='__main__':main()
