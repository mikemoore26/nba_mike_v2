"""Create a fail-closed, human-reviewed evidence ledger from S8.22.10.4.

This script NEVER verifies candidates automatically or authorizes training.
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

PDF_SHA = '18b5baaaccaf7b9e96529e40191432cd5ec2fc42ab3ca363e7d77d2a78c8873a'
# Independent game-ID-based slate as previously recorded, NOT automatically reconciled.
OFFICIAL_SLATE = {
 'DAL@WAS','ATL@NYK','PHI@BOS','TOR@MIL','CHI@ORL','PHX@MIN','LAL@SAC','POR@CLE'
}
# Prior S8.22.10.4 extraction uses a different orientation for some matchups.
# Do not assume either list is authoritative until original schedule evidence is reviewed.


def read_csv(path):
    with path.open('r',encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path,rows,fields):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)


def normalize_matchup(value):
    m=re.fullmatch(r'([A-Z]{2,3})@([A-Z]{2,3})',value.strip().upper())
    return (m.group(1),m.group(2)) if m else None


def schedule_check(date,game):
    if date!='2023-11-15':return 'OUTSIDE_TARGET_DATE'
    parsed=normalize_matchup(game)
    if parsed is None:return 'INVALID_OR_MISSING_MATCHUP'
    if game in OFFICIAL_SLATE:return 'EXACT_PRIOR_SLATE_MATCH'
    if f'{parsed[1]}@{parsed[0]}' in OFFICIAL_SLATE:return 'REVERSED_HOME_AWAY_CONFLICT'
    return 'NOT_IN_PRIOR_SLATE'


def pdf_fragments(pdf_bytes):
    reader=PdfReader(io.BytesIO(pdf_bytes))
    if reader.is_encrypted:raise ValueError('Encrypted PDF')
    pages=[]
    for page in reader.pages:
        items=[]
        def visitor(text,cm,tm,font_dict,font_size):
            value=' '.join(text.split())
            if value and 0<=tm[4]<=1100 and 0<=tm[5]<=2000:
                items.append((float(tm[5]),float(tm[4]),value))
        page.extract_text(visitor_text=visitor)
        pages.append(items)
    return pages


def evidence_excerpt(pages,page,y):
    if not (1<=page<=len(pages)):return ''
    nearby=[(yy,x,text) for yy,x,text in pages[page-1] if abs(yy-y)<=14.5 and 85<=yy<525]
    nearby.sort(key=lambda v:(round(v[0],1),v[1]))
    # This is context for manual review, not a certified reconstruction.
    return ' | '.join(f'{yy:.1f}:{text}' for yy,x,text in nearby)[:1800]


def make_ledger(players,submissions,pages):
    ledger=[]
    for kind,records in [('PLAYER',players),('TEAM_SUBMISSION',submissions)]:
        for idx,r in enumerate(records,1):
            page=int(r['page']); y=float(r['y'])
            date=r.get('game_date_candidate','');game=r.get('matchup_candidate','')
            name=r.get('player_name_candidate','') if kind=='PLAYER' else r.get('submission_text','')
            header_artifact=(kind=='PLAYER' and name.strip().lower()=='player name' and r.get('status_candidate','').strip().lower()=='current status')
            ledger.append({
                'record_id':f'{kind[:1]}-{idx:03d}', 'record_type':kind,'page':page,'y':r['y'],
                'game_date_candidate':date,'matchup_candidate':game,'team_candidate':r.get('team_candidate',''),
                'name_or_notice_candidate':name,'status_candidate':r.get('status_candidate',''),
                'reason_candidate':r.get('reason_candidate',''),
                'pdf_context_excerpt':evidence_excerpt(pages,page,y),
                'prior_schedule_comparison':schedule_check(date,game),
                'parser_header_artifact_flag':'YES' if header_artifact else 'NO',
                'manual_decision':'PENDING', 'reviewer':'', 'reviewed_at_utc':'',
                'verified_game_date':'','verified_matchup':'','verified_team':'',
                'verified_name_or_notice':'','verified_status':'','verified_reason':'',
                'review_notes':'', 'historical_asof_certified':'NO',
                'training_eligible':'NO'
            })
    return ledger


FIELDS=['record_id','record_type','page','y','game_date_candidate','matchup_candidate','team_candidate',
        'name_or_notice_candidate','status_candidate','reason_candidate','pdf_context_excerpt',
        'prior_schedule_comparison','parser_header_artifact_flag','manual_decision','reviewer','reviewed_at_utc',
        'verified_game_date','verified_matchup','verified_team','verified_name_or_notice',
        'verified_status','verified_reason','review_notes','historical_asof_certified','training_eligible']


def run(root,receipt_path,results_dir):
    root=root.resolve();receipt_path=receipt_path.resolve();results_dir=results_dir.resolve()
    if not receipt_path.is_relative_to(root) or not receipt_path.is_file():raise ValueError('Receipt must be a project file')
    if not results_dir.is_relative_to(root) or not results_dir.is_dir():raise ValueError('Results must be within project')
    receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
    if receipt.get('milestone')!='S8.22.10' or receipt.get('decision')!='BLOCK_TRAINING':raise ValueError('Unexpected receipt')
    pdf=(root/receipt['source_file']).resolve()
    if not pdf.is_relative_to(root) or pdf.parent!=receipt_path.parent or not pdf.is_file():raise ValueError('PDF path mismatch')
    pdf_bytes=pdf.read_bytes();sha=hashlib.sha256(pdf_bytes).hexdigest()
    if not pdf_bytes.startswith(b'%PDF-') or sha!=receipt['sha256'] or sha!=PDF_SHA:raise ValueError('PDF SHA mismatch')
    review=json.loads((results_dir/'review.json').read_text(encoding='utf-8'))
    if review.get('milestone')!='S8.22.10.4' or review.get('pdf_sha256')!=sha or review.get('decision')!='BLOCK_TRAINING':raise ValueError('S8.22.10.4 review mismatch')
    players=read_csv(results_dir/'player_status_candidates.csv')
    submissions=read_csv(results_dir/'team_submission_candidates.csv')
    if len(players)!=review['player_candidates'] or len(submissions)!=review['team_submission_candidates']:raise ValueError('CSV/review counts mismatch')
    pages=pdf_fragments(pdf_bytes)
    if len(pages)!=review['pages']:raise ValueError('Page count mismatch')
    ledger=make_ledger(players,submissions,pages)
    out=root/'research/p0_s8/s8_22_10_5/results/2023-11-15'/uuid.uuid4().hex
    out.mkdir(parents=True,exist_ok=False)
    write_csv(out/'manual_review_ledger.csv',ledger,FIELDS)
    flagged=[r for r in ledger if r['prior_schedule_comparison'] not in ('EXACT_PRIOR_SLATE_MATCH','OUTSIDE_TARGET_DATE') or r['parser_header_artifact_flag']=='YES']
    write_csv(out/'schedule_and_artifact_flags.csv',flagged,FIELDS)
    summary={'milestone':'S8.22.10.5','source_milestone':'S8.22.10.4','pdf_sha256':sha,
        'player_candidates':len(players),'team_submission_candidates':len(submissions),
        'review_rows':len(ledger),'manual_decisions_completed':0,'manual_decisions_pending':len(ledger),
        'schedule_or_artifact_flags':len(flagged),
        'reversed_home_away_conflicts':sum(r['prior_schedule_comparison']=='REVERSED_HOME_AWAY_CONFLICT' for r in ledger),
        'prior_schedule_is_not_certified':True,'source_publication_asof':'NOT_CERTIFIED',
        'player_identity':'NOT_CERTIFIED','eligibility_and_dnp':'NOT_CERTIFIED',
        'manual_table_review':'REQUIRED','decision':'BLOCK_TRAINING'}
    (out/'review.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',out/'review.json')
    for k,v in summary.items():print(k.upper().replace('_',' ')+':',v)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',default='.')
    p.add_argument('--receipt',required=True)
    p.add_argument('--s822104-results',required=True)
    a=p.parse_args()
    try:run(Path(a.project_root),Path(a.receipt),Path(a.s822104_results))
    except Exception as e:print('FAIL CLOSED:',e,file=sys.stderr);sys.exit(2)

if __name__=='__main__':main()
