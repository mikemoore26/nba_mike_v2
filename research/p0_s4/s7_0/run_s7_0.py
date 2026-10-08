"""Offline, no-network feasibility inventory. No sources claimed verified."""
from __future__ import annotations
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from nba_mike.data.pregame_audit import summarize_records

OUT = Path(__file__).parent / 'results'
REGISTRY = [
    {'family':'official injury reports', 'candidate':'NBA official injury report archives', 'status':'UNVERIFIED', 'asof_risk':'publication/revision times and historical archive completeness'},
    {'family':'lineups', 'candidate':'historical starting lineup announcements', 'status':'UNVERIFIED', 'asof_risk':'actual starters may be known only at tipoff'},
    {'family':'transactions/roster', 'candidate':'official roster and transaction logs', 'status':'UNVERIFIED', 'asof_risk':'effective date may differ from announcement date'},
    {'family':'game participation', 'candidate':'existing game logs', 'status':'RETROSPECTIVE_ONLY', 'asof_risk':'cannot use target-game minutes or participation before game'},
    {'family':'team rotation', 'candidate':'lagged prior-game minutes and availability', 'status':'REQUIRES_DERIVATION', 'asof_risk':'strictly exclude target game and later games'},
]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = []
    for path in sorted((ROOT/'research'/'p0_s4').rglob('*')):
        if path.is_file() and path.suffix.lower() in ('.csv','.parquet','.json'):
            rel = path.relative_to(ROOT).as_posix()
            if '/s7_0/results/' in '/' + rel: continue
            files.append({'path':rel, 'bytes':path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest() if path.stat().st_size < 20_000_000 else None})
    sample = Path(__file__).parent / 'candidate_observations.csv'
    rows=[]
    if sample.exists():
        with sample.open(newline='', encoding='utf-8-sig') as f:
            rows=list(csv.DictReader(f))
    result = {
        'status':'AUDIT_ONLY_NO_MODEL_PROMOTION',
        'sources':REGISTRY,
        'local_research_inventory':files,
        'observation_audit':summarize_records(rows),
        'gates':{
            'historical_injury_asof_source_verified':False,
            'historical_lineup_asof_source_verified':False,
            'DNP_population_defined':False,
            'pregame_cutoff_policy_finalized':False,
            'eligible_for_feature_training':False,
        },
        'next_actions':['verify licensing/access and historical as-of coverage',
                        'freeze prediction cutoff and update/revision rules',
                        'define player-game universe including DNPs',
                        'obtain historical source sample with publication timestamps',
                        'audit sample before modeling'],
    }
    dest=OUT/'s7_0_feasibility_report.json'
    dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('S7.0 AUDIT COMPLETE — no sources verified; no training authorization')
    print('local research files:',len(files))
    print('candidate rows:',result['observation_audit'])
    print('report:',dest)

if __name__=='__main__':main()
