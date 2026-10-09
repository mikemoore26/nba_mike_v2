"""S8.22.3: offline, evidence-aware provider authorization review."""
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

SOURCES = [
    dict(provider='balldontlie',schedule_endpoint='https://api.balldontlie.io/v1/games',docs='https://docs.balldontlie.io/',free_limit='5 requests/min',free_schedule='DOCUMENTED_YES',paid_entry_usd_month='9.99',id_namespace='PROVIDER_ID_NOT_NBA_ID',date_field='datetime',access='API_KEY_REQUIRED',permission='TERMS_REVIEW_REQUIRED',live_validation='NOT_TESTED',recommendation='FIRST_SANDBOX_CANDIDATE'),
    dict(provider='api_sports_nba',schedule_endpoint='https://v2.nba.api-sports.io/games',docs='https://api-sports.io/sports/nba',free_limit='100 requests/day (provider advertised)',free_schedule='CHECK_ACCOUNT_COVERAGE',paid_entry_usd_month='15.00',id_namespace='PROVIDER_ID_NOT_NBA_ID',date_field='CHECK_SCHEMA',access='API_KEY_REQUIRED',permission='TERMS_REVIEW_REQUIRED',live_validation='NOT_TESTED',recommendation='SECOND_SANDBOX_CANDIDATE'),
    dict(provider='nba_cdn',schedule_endpoint='https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json',docs='https://www.nba.com/',free_limit='UNKNOWN',free_schedule='UNKNOWN',paid_entry_usd_month='',id_namespace='NBA_ID_POTENTIAL',date_field='UNKNOWN',access='HTTP_403_PREVIOUSLY_OBSERVED',permission='NOT_APPROVED',live_validation='BLOCKED_HTTP_403',recommendation='DO_NOT_RETRY'),
]
GATES = [
    ('provider_terms','Provider terms reviewed for the intended automated use'),
    ('account_entitlement','User account and endpoint entitlement verified'),
    ('api_key_security','Secret stored outside source code, logs, and artifacts'),
    ('rate_limit','Rate and daily quota verified and enforced'),
    ('live_response','One explicitly authorized manual request succeeds'),
    ('schema','Response schema and game coverage validated'),
    ('ids','Provider IDs mapped to NBA IDs with collision checks'),
    ('tipoff','UTC tipoff verified and changes/versioning supported'),
    ('provenance','S8.21 raw bytes, receipt UTC, headers and SHA256 retained'),
]

def decide_provider(rows):
    assert rows and all('provider' in r for r in rows)
    return 'balldontlie' if any(r['provider']=='balldontlie' and r['free_schedule']=='DOCUMENTED_YES' for r in rows) else 'NONE'

def audit(root: Path):
    out = root/'research/p0_s8/s8_22_3/results'
    out.mkdir(parents=True, exist_ok=True)
    with (out/'s8_22_3_provider_matrix.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(SOURCES[0])); w.writeheader(); w.writerows(SOURCES)
    with (out/'s8_22_3_acceptance_gates.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['gate','requirement','status']); w.writeheader(); w.writerows(dict(gate=k,requirement=v,status='PENDING_EVIDENCE') for k,v in GATES)
    report={'milestone':'S8.22.3','generated_utc':datetime.now(timezone.utc).isoformat(),'mode':'DOCUMENTATION_ONLY_OFFLINE','recommended_for_manual_account_REVIEW':decide_provider(SOURCES),'approved_live_providers':[],'live_network_requests':0,'games_collected':0,'schedule_gates_satisfied':0,'schedule_gates_total':len(GATES),'next_action':'REVIEW_PROVIDER_TERMS_AND_CREATE_FREE_API_KEY_IF_ACCEPTABLE','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','limitations':['Public API documentation is not a legal determination of permitted usage','Pricing and quotas can change; confirm current account dashboard','No account entitlement, schema, game ID mapping, tipoff accuracy or live access verified','No NBA player eligibility evidence','No model training; 88 restart-period games remain blocked']}
    (out/'s8_22_3_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');a=p.parse_args()
    print(json.dumps(audit(Path(a.project_root).resolve()),indent=2))
if __name__=='__main__':main()
