"""Offline, fail-closed NBA date snapshot extraction and provider comparison."""
import argparse,csv,hashlib,json,re,uuid
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

class NextData(HTMLParser):
    def __init__(self):
        super().__init__();self.in_script=False;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag=='script' and dict(attrs).get('id')=='__NEXT_DATA__':self.in_script=True
    def handle_endtag(self,tag):
        if tag=='script':self.in_script=False
    def handle_data(self,data):
        if self.in_script:self.parts.append(data)

def utc(s):
    return datetime.fromisoformat(s.replace('Z','+00:00')).astimezone(timezone.utc)

def games_from_html(raw):
    p=NextData();p.feed(raw.decode('utf-8','replace'))
    if not p.parts:raise ValueError('NBA __NEXT_DATA__ missing')
    d=json.loads(''.join(p.parts))
    mods=d['props']['pageProps']['gameCardFeed']['modules']
    games=[]
    for mod in mods:
        for card in mod.get('cards',[]):
            x=card.get('cardData',{})
            if not all(k in x for k in ('gameId','homeTeam','awayTeam','gameTimeUtc')):continue
            games.append({'official_nba_game_id':str(x['gameId']),'home_team':x['homeTeam']['teamTricode'],'away_team':x['awayTeam']['teamTricode'],'tipoff_utc':x['gameTimeUtc']})
    ids=[g['official_nba_game_id'] for g in games]
    if not games or len(ids)!=len(set(ids)):raise ValueError('No games or duplicate game IDs')
    return games

def verify(root,receipt_path,date):
    r=json.loads(receipt_path.read_text(encoding='utf-8'))
    if r.get('date')!=date:raise ValueError('Receipt date mismatch')
    u=urlparse(r.get('source_url',''))
    if u.scheme!='https' or u.netloc.lower()!='www.nba.com' or u.path!='/games' or f'date={date}' not in u.query:raise ValueError('Unexpected official date source URL')
    rel=Path(r['evidence_path'])
    if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe evidence path')
    src=(root/rel).resolve()
    if not src.is_relative_to(root.resolve()):raise ValueError('Evidence escapes root')
    b=src.read_bytes()
    if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('Source hash/size mismatch')
    return r,b

def read_provider(path):
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def provider_teams(row):
    # Only recognize explicit unambiguous team-code fields; never guess from IDs.
    for a,b in [('home_team','away_team'),('home_team_abbreviation','away_team_abbreviation'),('home_team_tricode','away_team_tricode'),('home_abbreviation','away_abbreviation')]:
        if row.get(a) and row.get(b):return row[a].strip().upper(),row[b].strip().upper()
    return None

def run(root,date,receipt,provider=None):
    r,b=verify(root,receipt,date); games=games_from_html(b)
    source_date_ids=[g['official_nba_game_id'] for g in games]
    issues=[]; comparison=[]
    if provider:
        rows=read_provider(provider)
        for i,p in enumerate(rows):
            teams=provider_teams(p)
            if not teams:
                issues.append(f'provider row {i+1}: unrecognized team columns; comparison blocked');continue
            hits=[g for g in games if (g['home_team'],g['away_team'])==teams]
            if len(hits)!=1:
                issues.append(f'provider row {i+1}: matchup absent or ambiguous {teams}');continue
            g=hits[0];comparison.append({'provider_row':i+1,**g,'matchup_match':True})
        if len(comparison)!=len(games) or len(rows)!=len(games):issues.append('provider row count / unique matchup coverage mismatch')
        # Tipoffs are not checked without a verified provider timestamp field and format.
    else:issues.append('provider snapshot not supplied; cross-source comparison not performed')
    return {'milestone':'S8.22.7.7','date':date,'source_url':r['source_url'],'source_sha256':r['sha256'],'source_retrieved_utc':r['retrieved_utc'],'official_game_count':len(games),'official_games':games,'official_game_ids':source_date_ids,'provider_comparison':comparison,'issues':issues,'official_source_integrity':'PASS','official_date_listing':'EXTRACTED_CANDIDATE','provider_agreement':'CANDIDATE_MATCHUPS_ONLY' if provider and not issues else 'NOT_VERIFIED','tipoff_agreement':'NOT_VERIFIED','date_completeness':'NOT_CERTIFIED','historical_asof':'NOT_CERTIFIED','routine_collection_approved':False,'training_eligible':False,'decision':'BLOCK_TRAINING'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',required=True);p.add_argument('--date',required=True);p.add_argument('--date-receipt',required=True);p.add_argument('--provider-csv');a=p.parse_args()
    root=Path(a.project_root).resolve()
    def resolve(s):
        q=Path(s);return q if q.is_absolute() else root/q
    result=run(root,a.date,resolve(a.date_receipt),resolve(a.provider_csv) if a.provider_csv else None)
    out=root/'research/p0_s8/s8_22_7_7/results'/a.date;out.mkdir(parents=True,exist_ok=True)
    path=out/f'official_date_review_{uuid.uuid4().hex}.json';path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('OFFICIAL GAMES:',result['official_game_count']);print('PROVIDER AGREEMENT:',result['provider_agreement']);print('REPORT:',path);print('DECISION:',result['decision'])
if __name__=='__main__':main()
