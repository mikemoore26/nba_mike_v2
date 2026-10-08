"""S7.28: inspect captured NBA trade-tracker candidates without fabricating IDs or as-of evidence."""
import argparse,csv,hashlib,json,re,unicodedata
from collections import Counter
from datetime import date,datetime,timezone
from pathlib import Path

SOURCE_URL='https://www.nba.com/news/2025-26-nba-trade-tracker'
TEAM={'Atlanta':'ATL','Boston':'BOS','Brooklyn':'BKN','Charlotte':'CHA','Chicago':'CHI','Cleveland':'CLE','Dallas':'DAL','Denver':'DEN','Detroit':'DET','Golden State':'GSW','Houston':'HOU','Indiana':'IND','LA':'LAC','LA Clippers':'LAC','Los Angeles Clippers':'LAC','LA Lakers':'LAL','Los Angeles Lakers':'LAL','Memphis':'MEM','Miami':'MIA','Milwaukee':'MIL','Minnesota':'MIN','New Orleans':'NOP','New York':'NYK','Oklahoma City':'OKC','Orlando':'ORL','Philadelphia':'PHI','Phoenix':'PHX','Portland':'POR','Sacramento':'SAC','San Antonio':'SAS','Toronto':'TOR','Utah':'UTA','Washington':'WAS'}
OUT=['candidate_number','event_date','section','player_name','player_id','to_team','from_team','identity_status','origin_status','review_reason','source_url','source_sha256','retrieved_utc','evidence_class']
ASSET=re.compile(r'\b(?:draft|pick|picks|cash|considerations?|rights|swap|protected|future|second.round|first.round|exception)\b',re.I)
VIA=re.compile(r'^(.*?)\s*\(via\s+([^()]+)\)\s*$',re.I)
DATE=re.compile(r'\((Jan\.?|Feb\.?|Mar\.?|Apr\.?|May|Jun\.?|Jul\.?|Aug\.?|Sep\.?|Oct\.?|Nov\.?|Dec\.?)\s+(\d{1,2})\)\s*$',re.I)
MONTH={x:i for i,x in enumerate(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'],1)}

def norm(value):
    value=unicodedata.normalize('NFKD',value.replace('’',"'").replace('‘',"'"))
    return re.sub(r'[^a-z0-9]','', ''.join(c for c in value if not unicodedata.combining(c)).lower())

def parse_date(section,year=2026):
    m=DATE.search(section.strip())
    if not m:return ''
    try:return date(year,MONTH[m.group(1).lower().rstrip('.')[:3]],int(m.group(2))).isoformat()
    except ValueError:return ''

def destination(value):
    m=re.fullmatch(r'(.+?)\s+receives?:',value.strip(),re.I)
    return TEAM.get(m.group(1).strip()) if m else None

def load_ids(path):
    if not path:return {}
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames is None or set(reader.fieldnames)!=set(('player_id','player_name','source_url')):raise ValueError('ID map requires player_id,player_name,source_url columns')
        rows=list(reader)
    mapping={}
    for row in rows:
        if not row['player_id'].strip().isdigit() or not row['source_url'].startswith('https://') or not row['player_name'].strip():raise ValueError('Invalid player ID mapping evidence')
        key=norm(row['player_name']);mapping.setdefault(key,set()).add(row['player_id'].strip())
    return mapping

def inspect(candidates,source_html,id_map=None,output_dir=None):
    candidates=Path(candidates);source_html=Path(source_html)
    raw=source_html.read_bytes();sha=hashlib.sha256(raw).hexdigest()
    if not raw or b'<html' not in raw[:2000].lower() and b'<!doctype html' not in raw[:2000].lower():raise ValueError('Invalid source HTML')
    ids=load_ids(id_map)
    with candidates.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        required={'event_date','destination_team_text','player_text','source_url','source_sha256','retrieved_utc'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):raise ValueError('Missing S7.27 candidate fields')
        rows=list(reader)
    out=[];counts=Counter()
    for i,row in enumerate(rows,1):
        if row['source_sha256']!=sha or row['source_url']!=SOURCE_URL:raise ValueError(f'Candidate {i}: source provenance mismatch')
        section=row['event_date'].strip();player=row['player_text'].strip();dest=destination(row['destination_team_text']);m=VIA.fullmatch(player)
        if m:player=m.group(1).strip();origin=TEAM.get(m.group(2).strip())
        else:origin=None
        asset=bool(ASSET.search(player));date_str=parse_date(section)
        matching=ids.get(norm(player),set()) if not asset else set()
        player_id=next(iter(matching)) if len(matching)==1 else ''
        reasons=[]
        if asset:reasons.append('NON_PLAYER_ASSET')
        if not date_str:reasons.append('NO_EXPLICIT_SECTION_DATE')
        if not dest:reasons.append('UNKNOWN_DESTINATION')
        if not player_id:reasons.append('MISSING_OR_AMBIGUOUS_STABLE_ID')
        if not origin:reasons.append('NO_EXPLICIT_ORIGIN')
        if origin and dest==origin:reasons.append('SAME_ORIGIN_DESTINATION')
        if not asset and not re.search(r'[A-Za-z]',player):reasons.append('INVALID_PLAYER_TEXT')
        # Even fully structured rows cannot become S7.26 evidence: historical source publication timestamp is not verified.
        cls='REVIEW_ONLY_STRUCTURED' if not reasons else 'REVIEW_REQUIRED'
        item={'candidate_number':i,'event_date':date_str,'section':section,'player_name':player if not asset else '', 'player_id':player_id,'to_team':dest or '', 'from_team':origin or '', 'identity_status':'STABLE_ID_CANDIDATE' if player_id else 'UNRESOLVED','origin_status':'EXPLICIT_VIA' if origin else 'UNKNOWN','review_reason':';'.join(reasons) or 'HISTORICAL_SOURCE_PUBLICATION_UNVERIFIED','source_url':SOURCE_URL,'source_sha256':sha,'retrieved_utc':row['retrieved_utc'],'evidence_class':cls}
        out.append(item);counts[cls]+=1
    report={'milestone':'S7.28','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','source_sha256':sha,'input_candidates':len(rows),'review_only_structured':counts['REVIEW_ONLY_STRUCTURED'],'review_required':counts['REVIEW_REQUIRED'],'non_player_assets':sum('NON_PLAYER_ASSET' in r['review_reason'] for r in out),'dated_candidates':sum(bool(r['event_date']) for r in out),'resolved_player_ids':sum(bool(r['player_id']) for r in out),'explicit_origin_rows':sum(bool(r['from_team']) for r in out),'qualified_s726_events':0,'verified_injury_assignments':0,'historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['Trade tracker section dates are parsed from page headings, not independently authenticated effective dates','Via text is the reported origin, not a validated complete transaction chain','Player IDs require independent user-supplied mapping; no fuzzy or fabricated IDs','No source publication timestamp proven for the historical prediction cutoff','No export to S7.26 or S7.23']}
    if output_dir:
        dest=Path(output_dir);dest.mkdir(parents=True,exist_ok=True)
        with (dest/'s7_28_review.csv').open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=OUT);writer.writeheader();writer.writerows(out)
        (dest/'s7_28_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report,out

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidates',default='research/p0_s4/s7_27/results/s7_27_candidates.csv');p.add_argument('--source-html');p.add_argument('--id-map');p.add_argument('--output-dir',default='research/p0_s4/s7_28/results');a=p.parse_args()
    try:
        if a.source_html:source=a.source_html
        else:
            folder=Path('research/p0_s4/s7_27/results/objects');files=list(folder.glob('*.html'))
            if len(files)!=1:raise ValueError('Specify --source-html when zero or multiple HTML snapshots exist')
            source=files[0]
        report,_=inspect(a.candidates,source,a.id_map,a.output_dir);print(json.dumps(report,indent=2))
    except (ValueError,OSError,KeyError) as exc:
        print(json.dumps({'milestone':'S7.28','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(exc)}));raise SystemExit(1)
if __name__=='__main__':main()
