"""S8.22.10.20: offline authoritative-registry candidate reconciliation (never certification)."""
import argparse,csv,hashlib,json,re,unicodedata
from collections import Counter,defaultdict
from pathlib import Path
DATE='2023-11-15'
LEDGER_SHA='70cc499b1c35cd65cde2ce0c8836e1db13e9194a43ac290450755f067ff3c3db'
SOURCE_DIAGNOSTIC_SHA='5c5e3471673d639e0cd1e6cb97dcf747157eaa7bfe274edd29c32cf8e76ab092'
FIELDS=['record_id','raw_name','team_candidate','local_name_match','registry_match_class','candidate_nba_person_id','registry_display_name','registry_team','reason','player_identity_certified','injury_status_certified','historical_asof_certified']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:
        d=csv.DictReader(f)
        if not d.fieldnames:raise ValueError('Missing CSV header: '+str(p))
        return list(d)
def locate(root,stage,name,expected=None):
    paths=sorted((root/'research/p0_s8'/stage/'results'/DATE).glob('*/'+name))
    matched=[p for p in paths if expected is None or sha(p)==expected]
    if len(matched)!=1:raise ValueError(f'Expected one unique {stage}/{name}'+(' with verified hash' if expected else '')+f'; got {len(matched)}')
    return matched[0]
def normalized(name):
    s=unicodedata.normalize('NFKD',name or '').casefold()
    s=''.join(c for c in s if not unicodedata.combining(c))
    if ',' in s:
        last,first=s.split(',',1);s=first+' '+last
    return ' '.join(re.findall(r'[^\W_]+',s,flags=re.UNICODE))
def parse_registry(raw):
    """Accept raw NBA stats CommonAllPlayers response, not arbitrary ID-name dictionaries."""
    if not isinstance(raw,dict) or 'resultSets' not in raw:raise ValueError('Expected raw NBA stats CommonAllPlayers resultSets JSON')
    sets=raw['resultSets']
    if isinstance(sets,dict):sets=[dict(name=k,headers=v.get('headers',[]),rowSet=v.get('rowSet',[])) for k,v in sets.items()]
    candidates=[s for s in sets if str(s.get('name','')).casefold()=='commonallplayers']
    if len(candidates)!=1:raise ValueError('Expected one CommonAllPlayers result set')
    s=candidates[0];headers=s.get('headers',[])
    if len(headers)!=len(set(headers)) or not {'PERSON_ID','DISPLAY_FIRST_LAST','TEAM_ABBREVIATION'}.issubset(headers):raise ValueError('Missing/duplicate required NBA registry columns')
    out=[]
    for row in s.get('rowSet',[]):
        if len(row)!=len(headers):raise ValueError('Malformed registry row')
        d=dict(zip(headers,row));pid=str(d['PERSON_ID']).strip();name=str(d['DISPLAY_FIRST_LAST'] or '').strip()
        if not pid.isdecimal() or not name:raise ValueError('Invalid registry person ID or name')
        out.append(dict(id=pid,name=name,team=str(d['TEAM_ABBREVIATION'] or '').strip().upper()))
    if not out:raise ValueError('Empty registry')
    return out
def reconcile(ledger,corroboration,registry=None):
    players=[r for r in ledger if r.get('record_type')=='PLAYER']
    if len(ledger)!=54 or len(players)!=44 or len(corroboration)!=44:raise ValueError('Expected 54 ledger records, 44 player candidates and 44 corroboration rows')
    by_id={r.get('record_id'):r for r in players};by_c={r.get('record_id'):r for r in corroboration}
    if len(by_id)!=44 or len(by_c)!=44 or set(by_id)!=set(by_c):raise ValueError('Duplicate/mismatched record IDs')
    index=defaultdict(list)
    for r in registry or []:index[normalized(r['name'])].append(r)
    output=[]
    for rid in sorted(by_id):
        r=by_id[rid];c=by_c[rid];name=r.get('name_or_notice_candidate','')
        if c.get('raw_name')!=name:raise ValueError('Local corroboration name mismatch: '+rid)
        if c.get('local_name_corrob')!='YES' or c.get('match_class') not in ('LOCAL_NAME_MATCH','LOCAL_NAME_REORDERED'):raise ValueError('Local corroboration not established: '+rid)
        team=(r.get('team_candidate') or '').strip().upper()
        options=index.get(normalized(name),[])
        ids={o['id'] for o in options}
        if registry is None:klass='REGISTRY_NOT_SUPPLIED';reason='Awaiting raw official registry evidence';chosen=[]
        elif not options:klass='NO_REGISTRY_NAME_MATCH';reason='No exact normalized name match';chosen=[]
        elif len(ids)!=1:klass='AMBIGUOUS_REGISTRY_NAME';reason='Name matches multiple person IDs';chosen=[]
        else:
            chosen=[o for o in options if o['id'] in ids]
            registry_teams={o['team'] for o in chosen if o['team']}
            if not team:klass='TEAM_NOT_IN_LEDGER';reason='Cannot independently cross-check historical team'
            elif not registry_teams:klass='REGISTRY_TEAM_MISSING';reason='Registry contains no team value'
            elif team not in registry_teams:klass='TEAM_MISMATCH_REVIEW';reason='Name matched but source team differs from registry team'
            else:klass='NAME_TEAM_CANDIDATE';reason='Unique name/person ID and same team in supplied registry; historical season and provenance still unverified'
        safe=chosen[0] if chosen and klass=='NAME_TEAM_CANDIDATE' else None
        output.append(dict(record_id=rid,raw_name=name,team_candidate=team,local_name_match='YES',registry_match_class=klass,candidate_nba_person_id=safe['id'] if safe else '',registry_display_name=safe['name'] if safe else '',registry_team=safe['team'] if safe else '',reason=reason,player_identity_certified='NO',injury_status_certified='NO',historical_asof_certified='NO'))
    return output
def run(root,registry_path=None):
    root=root.resolve();ledger=locate(root,'s8_22_10_7','player_and_team_manual_review.csv',LEDGER_SHA)
    corroboration=locate(root,'s8_22_10_19','name_corroboration.csv')
    diagnostic=locate(root,'s8_22_10_18','name_layout_diagnostics.csv',SOURCE_DIAGNOSTIC_SHA)
    source_report=corroboration.parent/'review.json'
    if not source_report.is_file():raise ValueError('Missing S8.22.10.19 report')
    report=json.loads(source_report.read_text(encoding='utf-8'))
    if report.get('source_diagnostic_sha256')!=sha(diagnostic) or report.get('source_ledger_sha256')!=sha(ledger) or report.get('locally_corrob')!=44 or report.get('training_decision')!='BLOCK_TRAINING':raise ValueError('Prior milestone provenance invalid')
    registry=None
    if registry_path:
        registry_path=registry_path.resolve()
        registry=parse_registry(json.loads(registry_path.read_text(encoding='utf-8')))
    rows=reconcile(readcsv(ledger),readcsv(corroboration),registry)
    source_hashes=dict(ledger=sha(ledger),corroboration=sha(corroboration),diagnostic=sha(diagnostic),registry=sha(registry_path) if registry_path else None)
    token=hashlib.sha256(json.dumps(source_hashes,sort_keys=True).encode()+b'S8.22.10.20-v1').hexdigest()[:16]
    out=root/'research/p0_s8/s8_22_10_20/results'/DATE/token;out.mkdir(parents=True,exist_ok=True)
    with (out/'player_registry_candidates.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    summary=dict(milestone='S8.22.10.20',game_date=DATE,source_hashes=source_hashes,registry_supplied=registry is not None,registry_file=str(registry_path) if registry_path else None,registry_format='NBA stats CommonAllPlayers raw JSON' if registry is not None else None,player_candidates=44,team_notices_excluded=10,classification_counts=dict(sorted(Counter(r['registry_match_class'] for r in rows).items())),candidate_ids_proposed=sum(bool(r['candidate_nba_person_id']) for r in rows),player_ids_certified=0,injury_statuses_certified=0,historical_asof_certified=0,research_status='RESEARCH_ONLY',training_decision='BLOCK_TRAINING',next_action='Obtain official historical-season registry JSON and independently verify its provenance, capture date, season, player identity and historical team. Candidate matches are not certification.',note='No online fetch, no generated player IDs, no source modifications. Registry absent means inventory only.')
    (out/'review.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',out/'review.json');print(json.dumps(summary,indent=2));return summary
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');p.add_argument('--registry-json',type=Path,help='Optional unmodified official NBA stats CommonAllPlayers JSON; verify source provenance separately');a=p.parse_args()
    try:run(Path(a.project_root),a.registry_json)
    except (ValueError,KeyError,FileNotFoundError,UnicodeError,json.JSONDecodeError) as e:p.exit(2,'FAIL CLOSED: '+str(e)+'\n')
