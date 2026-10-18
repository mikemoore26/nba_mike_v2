"""Local installed nba_api registry capture and name-only candidate reconciliation."""
import argparse,csv,datetime as dt,hashlib,importlib.metadata as md,importlib.util,json,sys
from collections import Counter,defaultdict
from pathlib import Path

DATE='2023-11-15'
def digest(b):return hashlib.sha256(b).hexdigest()
def immutable(path,b):
    if path.exists() and path.read_bytes()!=b:raise ValueError('Immutable capture conflict: '+str(path))
    if not path.exists():path.write_bytes(b)
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:raise ValueError('Missing module: '+str(path))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def local_snapshot():
    from nba_api.stats.static import players
    version=md.version('nba_api')
    module=Path(players.__file__).resolve()
    if not module.is_file():raise ValueError('Installed players module not found')
    data=players.get_players()
    if not isinstance(data,list) or not data:raise ValueError('Empty local registry')
    normalized=[];seen=set()
    for r in data:
        if not isinstance(r,dict) or isinstance(r.get('id'),bool) or not isinstance(r.get('id'),int) or r['id']<=0 or not isinstance(r.get('full_name'),str) or not r['full_name'].strip():raise ValueError('Malformed installed player record')
        if r['id'] in seen:raise ValueError('Duplicate NBA ID')
        seen.add(r['id']);normalized.append({'id':r['id'],'full_name':r['full_name'].strip()})
    blob=(json.dumps(normalized,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
    return blob,{'package':'nba_api','package_version':version,'module_path':str(module),'module_sha256':digest(module.read_bytes()),'capture_method':'installed nba_api.stats.static.players.get_players()','module_file_name':module.name}
def candidates(ledger,corroboration,registry,normalizer):
    players={r['record_id']:r for r in ledger if r.get('record_type')=='PLAYER'}
    cor={r['record_id']:r for r in corroboration}
    if len(ledger)!=54 or len(players)!=44 or len(corroboration)!=44 or len(cor)!=44 or len(cor)!=len(corroboration) or set(players)!=set(cor):raise ValueError('Historical ledger/corroboration cardinality mismatch')
    idx=defaultdict(list)
    for p in registry:idx[normalizer(p['full_name'])].append(p)
    rows=[]
    for rid in sorted(players):
        r=players[rid];c=cor[rid];name=r['name_or_notice_candidate']
        if c.get('raw_name')!=name or c.get('local_name_corrob')!='YES' or c.get('match_class') not in ('LOCAL_NAME_MATCH','LOCAL_NAME_REORDERED'):raise ValueError('Uncorroborated player: '+rid)
        hits=idx.get(normalizer(name),[])
        cls='NO_NAME_MATCH' if not hits else ('AMBIGUOUS_NAME_MATCH' if len(hits)!=1 else 'UNIQUE_NAME_ID_CANDIDATE')
        rows.append({'record_id':rid,'raw_name':name,'report_team':r.get('team_candidate',''),'match_class':cls,'candidate_nba_person_id':str(hits[0]['id']) if len(hits)==1 else '', 'registry_full_name':hits[0]['full_name'] if len(hits)==1 else '', 'candidate_count':len(hits),'historical_team_verified':'NO','player_identity_certified':'NO','injury_status_certified':'NO','historical_asof_certified':'NO'})
    return rows
def run(root):
    root=Path(root).resolve()
    prior=load(root/'research/p0_s8/s8_22_10_20/run_s8_22_10_20.py','s8221020_local_bridge')
    ledger=prior.locate(root,'s8_22_10_7','player_and_team_manual_review.csv',prior.LEDGER_SHA)
    cor=prior.locate(root,'s8_22_10_19','name_corroboration.csv')
    diag=prior.locate(root,'s8_22_10_18','name_layout_diagnostics.csv',prior.SOURCE_DIAGNOSTIC_SHA)
    report=json.loads((cor.parent/'review.json').read_text(encoding='utf-8'))
    if report.get('source_ledger_sha256')!=prior.sha(ledger) or report.get('source_diagnostic_sha256')!=prior.sha(diag) or report.get('locally_corrob')!=44 or report.get('training_decision')!='BLOCK_TRAINING':raise ValueError('Historical provenance gate failed')
    blob,provenance=local_snapshot();registry=json.loads(blob)
    rows=candidates(prior.readcsv(ledger),prior.readcsv(cor),registry,prior.normalized)
    token=digest(blob)[:16]
    dest=root/'research/p0_s8/s8_22_10_22a/results'/DATE/token;dest.mkdir(parents=True,exist_ok=True)
    raw=dest/'installed_nba_api_players.json';immutable(raw,blob)
    bridge={'resultSets':[{'name':'CommonAllPlayers','headers':['PERSON_ID','DISPLAY_FIRST_LAST','TEAM_ABBREVIATION'],'rowSet':[[r['id'],r['full_name'],''] for r in registry]}]}
    adapter=dest/'third_party_name_only_adapter.json';immutable(adapter,(json.dumps(bridge,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
    fields=list(rows[0]);import io
    buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=fields);w.writeheader();w.writerows(rows)
    outcsv=dest/'player_id_candidates.csv';immutable(outcsv,buf.getvalue().encode())
    counts=dict(sorted(Counter(r['match_class'] for r in rows).items()))
    manifest={'milestone':'S8.22.10.22A','target_game_date':DATE,'capture_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_class':'THIRD_PARTY_INSTALLED_PACKAGE_NOT_HISTORICAL','source_provenance':provenance,'raw_sha256':digest(blob),'raw_count':len(registry),'unique_ids':len(registry),'adapter_sha256':digest(adapter.read_bytes()),'candidate_csv_sha256':digest(outcsv.read_bytes()),'ledger_sha256':prior.sha(ledger),'corroboration_sha256':prior.sha(cor),'diagnostic_sha256':prior.sha(diag),'classification_counts':counts,'unique_name_id_candidates':counts.get('UNIQUE_NAME_ID_CANDIDATE',0),'player_ids_certified':0,'historical_team_verified':0,'injury_statuses_certified':0,'historical_asof_certified':0,'research_status':'RESEARCH_ONLY','training_decision':'BLOCK_TRAINING','note':'Installed third-party static player list is mutable and not a 2023 historical roster. Candidate IDs only; no historical team or injury certification.'}
    mf=dest/'capture_manifest.json'
    if mf.exists():
        old=json.loads(mf.read_text(encoding='utf-8'))
        if any(old.get(k)!=manifest[k] for k in ('raw_sha256','adapter_sha256','candidate_csv_sha256','ledger_sha256','corroboration_sha256')):raise ValueError('Existing manifest conflicts with evidence')
    else:mf.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',mf);print(json.dumps(manifest,indent=2));return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args()
    try:run(a.project_root)
    except (ValueError,ImportError,OSError,KeyError,TypeError,json.JSONDecodeError) as e:p.exit(2,'FAIL CLOSED: '+str(e)+'\n')
