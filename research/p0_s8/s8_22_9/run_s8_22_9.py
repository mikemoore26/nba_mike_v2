"""Offline provider feasibility qualification; never authorizes training."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

CATEGORIES = {'player_availability', 'expected_minutes', 'starting_lineups', 'player_opportunity', 'betting_markets'}
REQUIRED = {'id','name','rank','categories','url','documented_capability','historical_2023_access','pregame_timestamp_proof','cost','rights','next_action'}

def assess(data):
    problems=[]
    sources=data.get('candidate_sources', [])
    seen=set()
    for item in sources:
        missing=REQUIRED-set(item)
        if missing: problems.append(f"{item.get('id','?')}: missing {sorted(missing)}")
        key=item.get('id')
        if not key or key in seen: problems.append(f'duplicate/blank source id: {key}')
        seen.add(key)
        if not set(item.get('categories', [])).issubset(CATEGORIES): problems.append(f'{key}: invalid category')
        if not str(item.get('url','')).startswith('https://'): problems.append(f'{key}: invalid reference URL')
        if item.get('pregame_timestamp_proof') == 'VERIFIED' and not item.get('timestamp_evidence_receipt_sha256'):
            problems.append(f'{key}: pregame VERIFIED lacks archived receipt hash')
    coverage={c:[s.get('id') for s in sources if c in s.get('categories', [])] for c in sorted(CATEGORIES)}
    return {'milestone':'S8.22.9','candidate_count':len(sources),'coverage':coverage,
            'issues':problems,'source_shortlist_status':'REVIEW_READY' if not problems else 'INVALID',
            'historical_asof':'NOT_CERTIFIED','provider_access':'NOT_APPROVED',
            'training_eligible':False,'decision':'BLOCK_TRAINING'}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--project-root',default='.')
    ap.add_argument('--catalog',default='research/p0_s8/s8_22_9/source_candidates.json')
    args=ap.parse_args()
    root=Path(args.project_root).resolve()
    catalog=Path(args.catalog)
    if not catalog.is_absolute(): catalog=root/catalog
    raw=catalog.read_bytes()
    result=assess(json.loads(raw))
    result['catalog_sha256']=hashlib.sha256(raw).hexdigest()
    result['created_utc']=datetime.now(timezone.utc).isoformat()
    out=root/'research/p0_s8/s8_22_9/results'
    out.mkdir(parents=True,exist_ok=True)
    dest=out/f"source_qualification_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',dest)
    print('CANDIDATES:',result['candidate_count'])
    print('STATUS:',result['source_shortlist_status'])
    for category, ids in result['coverage'].items(): print(category+':',', '.join(ids))
    print('ISSUES:',result['issues'])
    print('DECISION:',result['decision'])
    return 1 if result['issues'] else 0

if __name__=='__main__': raise SystemExit(main())
