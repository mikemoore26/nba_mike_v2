"""S8.22.7.12 offline independent TV-listing evidence intake. No network calls."""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from uuid import uuid4

SOURCE_URL = 'https://sportsgamestoday.com/2023-11-15-wednesday-sports.php'
CITY = {'Dallas':'DAL','Washington':'WAS','Boston':'BOS','Philadelphia':'PHI',
        'Milwaukee':'MIL','Toronto':'TOR','New York':'NYK','Atlanta':'ATL',
        'Orlando':'ORL','Chicago':'CHI','Minnesota':'MIN','Phoenix':'PHX',
        'Sacramento':'SAC','LA Lakers':'LAL','Cleveland':'CLE','Portland':'POR'}

class Rows(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.row=None; self.cell=None; self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.skip+=1
        if tag=='tr': self.row=[]
        if tag in ('td','th') and self.row is not None: self.cell=[]
    def handle_data(self, data):
        if not self.skip and self.cell is not None: self.cell.append(data)
    def handle_endtag(self, tag):
        if tag in ('script','style') and self.skip: self.skip-=1
        if tag in ('td','th') and self.cell is not None:
            self.row.append(' '.join(' '.join(self.cell).split())); self.cell=None
        if tag=='tr' and self.row is not None:
            self.rows.append(self.row); self.row=None

def parse_tv_listing(raw):
    p=Rows(); p.feed(raw.decode('utf-8', errors='replace'))
    active=False; seen_header=False; matches=[]; issues=[]
    for row in p.rows:
        text=' '.join(row)
        if 'NBA REGULAR SEASON' in text.upper(): active=True; seen_header=True; continue
        if not active: continue
        if re.search(r'\b(?:NHL|COLLEGE FOOTBALL|MEN.S COLLEGE|WNBA)\b',text,re.I): break
        m=re.search(r'\b([A-Za-z ]+?)\s+at\s+([A-Za-z ]+?)\s*$',row[0] if row else '')
        if not m: continue
        away,home=(x.strip() for x in m.groups())
        if away not in CITY or home not in CITY:
            issues.append('UNKNOWN_TEAM:'+away+'@'+home); continue
        matches.append({'away_team':CITY[away],'home_team':CITY[home], 'listing':row[0]})
    if not seen_header: issues.append('NBA_SECTION_NOT_FOUND')
    if len(matches)!=len(set((r['away_team'],r['home_team']) for r in matches)):
        issues.append('DUPLICATE_MATCHUP')
    return matches,issues

def audit(raw, prior):
    found,issues=parse_tv_listing(raw)
    expected=prior.get('reconstructed_matches',[])
    if prior.get('date')!='2023-11-15' or prior.get('game_agreement')!='PASS':
        issues.append('PRIOR_GOVERNANCE_NOT_VALID')
    a={(r['away_team'],r['home_team']) for r in found}
    b={(r['away_team'],r['home_team']) for r in expected}
    if len(expected)!=8 or len(found)!=8: issues.append('EIGHT_GAME_COUNT_MISMATCH')
    if a!=b: issues.append('MATCHUP_SET_MISMATCH')
    return {'independent_listing_games':len(found),'prior_official_games':len(expected),
            'matchups_agree':a==b and len(found)==len(expected)==8,
            'matched_pairs':sorted([f'{x[0]}@{x[1]}' for x in a & b]),
            'issues':issues,
            'status':('CANDIDATE_INDEPENDENT_SLATE_CORROBORATION_REVIEW_REQUIRED' if not issues else 'BLOCKED_EVIDENCE_REVIEW'),
            'date_completeness':'NOT_CERTIFIED','historical_asof':'NOT_CERTIFIED',
            'training_eligible':False,'routine_collection_approved':False,'decision':'BLOCK_TRAINING'}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project-root',required=True)
    ap.add_argument('--source',required=True,help='Locally saved, unmodified HTML bytes')
    ap.add_argument('--governance-report',required=True)
    ap.add_argument('--retrieved-utc',required=True,help='Actual UTC retrieval time, ISO 8601')
    args=ap.parse_args()
    dt=datetime.fromisoformat(args.retrieved_utc.replace('Z','+00:00'))
    if dt.tzinfo is None or dt.utcoffset().total_seconds()!=0: ap.error('retrieved-utc must be UTC')
    root=Path(args.project_root).resolve()
    source=Path(args.source).resolve(); priorpath=Path(args.governance_report).resolve()
    raw=source.read_bytes(); prior_raw=priorpath.read_bytes(); prior=json.loads(prior_raw)
    result=audit(raw,prior)
    result.update({'milestone':'S8.22.7.12','date':'2023-11-15',
                   'source_url':SOURCE_URL,'source_retrieved_utc':dt.isoformat(),
                   'source_sha256':hashlib.sha256(raw).hexdigest(),
                   'source_bytes':len(raw),'prior_report_sha256':hashlib.sha256(prior_raw).hexdigest(),
                   'provenance_note':'Manual acquisition; no authenticated historical publication timestamp established. Listing may be retrospective.'})
    folder=root/'research/p0_s8/s8_22_7_12/evidence/2023-11-15'/uuid4().hex
    folder.mkdir(parents=True,exist_ok=False)
    (folder/'source.bin').write_bytes(raw)
    (folder/'review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('ARCHIVED:',folder)
    print('MATCHUPS:',result['independent_listing_games'],'AGREEMENT:',result['matchups_agree'])
    print('STATUS:',result['status'],'ISSUES:',result['issues'])
    print('DECISION:',result['decision'])

if __name__=='__main__': main()
