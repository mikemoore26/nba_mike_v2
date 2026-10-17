"""Read-only, date-aware schedule reconciliation. No model-training approval."""
import argparse, csv, hashlib, json, pathlib, re
from collections import Counter

# Independent historical schedule: Basketball-Reference 2023-24 November schedule.
# Game IDs are deliberately excluded: they require separate NBA.com verification.
SCHEDULE = {
 ('2023-11-15','DAL@WAS'), ('2023-11-15','NYK@ATL'),
 ('2023-11-15','BOS@PHI'), ('2023-11-15','MIL@TOR'),
 ('2023-11-15','ORL@CHI'), ('2023-11-15','MIN@PHX'),
 ('2023-11-15','SAC@LAL'), ('2023-11-15','CLE@POR'),
 ('2023-11-16','BKN@MIA'), ('2023-11-16','OKC@GSW'),
}
SOURCE = 'https://www.basketball-reference.com/leagues/NBA_2024_games-november.html'
NBA_CLE = 'https://www.nba.com/game/cle-vs-por-0022300199'

def classify(date, matchup):
    if not date or not matchup: return 'MISSING_DATE_OR_MATCHUP'
    if (date, matchup) in SCHEDULE: return 'CORROBORATED_ORIENTATION'
    if '@' not in matchup: return 'INVALID_MATCHUP'
    a,b=matchup.split('@',1)
    if (date, b+'@'+a) in SCHEDULE: return 'REVERSED_VS_EXTERNAL_SCHEDULE'
    return 'NOT_IN_EXTERNAL_SCHEDULE_SCOPE'

def find_input(root):
    candidates=list((root/'research/p0_s8/s8_22_10_5/results/2023-11-15').glob('*/manual_review_ledger.csv'))
    if len(candidates)!=1:
        raise RuntimeError(f'Expected exactly one S8.22.10.5 ledger; found {len(candidates)}. Use --ledger.')
    return candidates[0]

def run(root, ledger, out):
    with ledger.open(newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    if not rows: raise ValueError('Empty input ledger')
    required={'record_id','game_date_candidate','matchup_candidate'}
    missing=required-set(rows[0]);
    if missing: raise ValueError(f'Missing ledger fields: {sorted(missing)}')
    if len({r['record_id'] for r in rows})!=len(rows): raise ValueError('Duplicate record IDs')
    keys={(r['game_date_candidate'],r['matchup_candidate']) for r in rows}
    cross=[]
    for date,match in sorted(keys):
        status=classify(date,match)
        cross.append({'game_date':date,'pdf_matchup':match,'external_matchup':match if status=='CORROBORATED_ORIENTATION' else '',
                      'external_status':status,'record_count':sum(r['game_date_candidate']==date and r['matchup_candidate']==match for r in rows),
                      'evidence_url':NBA_CLE if date=='2023-11-15' and match=='CLE@POR' else SOURCE,
                      'game_id_verified':'NO','manual_review':'PENDING'})
    annotated=[]
    for row in rows:
        r=dict(row); r['s822106_schedule_status']=classify(row['game_date_candidate'],row['matchup_candidate']);
        r['s822106_manual_decision']='PENDING';annotated.append(r)
    out.mkdir(parents=True,exist_ok=True)
    def write(name, data, fields):
        with (out/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(data)
    write('unique_matchup_reconciliation.csv',cross,list(cross[0]))
    write('annotated_review_ledger.csv',annotated,list(annotated[0]))
    review={'milestone':'S8.22.10.6','source_ledger':str(ledger),'source_sha256':hashlib.sha256(ledger.read_bytes()).hexdigest(),
            'record_count':len(rows),'unique_matchups':len(cross), 'matchup_status_counts':dict(Counter(r['external_status'] for r in cross)),
            'record_status_counts':dict(Counter(r['s822106_schedule_status'] for r in annotated)),
            'historical_asof':'NOT_CERTIFIED','player_identity':'NOT_CERTIFIED','game_id_verified':'NO',
            'manual_reviews_completed':0,'decision':'BLOCK_TRAINING',
            'warning':'Independent historical schedule corroboration is not a publication-time or game-ID certification.'}
    (out/'review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
    return review

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');p.add_argument('--ledger');p.add_argument('--output')
    args=p.parse_args();root=pathlib.Path(args.project_root).resolve()
    ledger=pathlib.Path(args.ledger).resolve() if args.ledger else find_input(root)
    out=pathlib.Path(args.output).resolve() if args.output else root/'research/p0_s8/s8_22_10_6/results/2023-11-15'/hashlib.sha256(ledger.read_bytes()).hexdigest()[:16]
    review=run(root,ledger,out)
    print('REPORT:',out/'review.json');print(json.dumps(review,indent=2))
if __name__=='__main__': main()
