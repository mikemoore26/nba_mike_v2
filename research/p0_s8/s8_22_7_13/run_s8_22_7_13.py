"""Offline, fail-closed source-governance review for the 2023-11-15 slate."""
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

EXPECTED_DATE = '2023-11-15'
EXPECTED_URL = 'https://sportsgamestoday.com/2023-11-15-wednesday-sports.php'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def review(source_bytes, intake, governance, intake_bytes, governance_bytes):
    issues=[]
    def check(name, condition):
        if not condition: issues.append(name)
    check('SOURCE_HASH_MISMATCH', sha(source_bytes)==intake.get('source_sha256'))
    check('SOURCE_LENGTH_MISMATCH', len(source_bytes)==intake.get('source_bytes'))
    check('SOURCE_URL_MISMATCH', intake.get('source_url')==EXPECTED_URL)
    check('DATE_MISMATCH', intake.get('date')==EXPECTED_DATE and governance.get('date')==EXPECTED_DATE)
    check('INTAKE_STATUS_NOT_CANDIDATE', intake.get('status')=='CANDIDATE_INDEPENDENT_SLATE_CORROBORATION_REVIEW_REQUIRED' and not intake.get('issues'))
    check('INTAKE_MATCHUPS_INVALID', intake.get('matchups_agree') is True and intake.get('independent_listing_games')==8 and intake.get('prior_official_games')==8 and len(set(intake.get('matched_pairs',[])))==8)
    check('GOVERNANCE_NOT_PASS', governance.get('game_agreement')=='PASS' and len(governance.get('reconstructed_matches',[]))==8 and not governance.get('issues'))
    check('PRIOR_REPORT_HASH_MISMATCH', intake.get('prior_report_sha256')==sha(governance_bytes))
    expected={r.get('away_team','')+'@'+r.get('home_team','') for r in governance.get('reconstructed_matches',[])}
    check('MATCHUPS_DIFFER_FROM_PRIOR', set(intake.get('matched_pairs',[]))==expected and len(expected)==8)
    try:
        dt=datetime.fromisoformat(intake['source_retrieved_utc'].replace('Z','+00:00'))
        check('INVALID_RETRIEVAL_UTC', dt.tzinfo is not None and dt.utcoffset().total_seconds()==0)
    except (ValueError,KeyError,AttributeError): issues.append('INVALID_RETRIEVAL_UTC')
    return {
        'milestone':'S8.22.7.13','date':EXPECTED_DATE,'mode':'OFFLINE_SOURCE_GOVERNANCE_REVIEW',
        'source_url':EXPECTED_URL,'source_sha256':sha(source_bytes),
        'intake_review_sha256':sha(intake_bytes),'prior_governance_sha256':sha(governance_bytes),
        'checks':{'archived_evidence_integrity':'PASS' if not issues else 'FAIL',
                  'publisher_distinct_from_nba_and_provider':'OBSERVED_DISTINCT_DOMAIN',
                  'upstream_editorial_independence':'NOT_VERIFIED',
                  'eight_matchup_corroboration':'PASS' if not issues else 'BLOCKED',
                  'exhaustive_slate_claim':'NOT_ESTABLISHED',
                  'contemporaneous_publication':'NOT_ESTABLISHED',
                  'historical_pregame_availability':'NOT_ESTABLISHED'},
        'issues':issues,
        'status':'SOURCE_INTEGRITY_VERIFIED_SCOPE_LIMITED_REVIEW_REQUIRED' if not issues else 'BLOCKED_SOURCE_INTEGRITY',
        'retrospective_date_completeness':'NOT_CERTIFIED',
        'historical_asof':'NOT_CERTIFIED',
        'routine_collection_approved':False,'training_eligible':False,'decision':'BLOCK_TRAINING',
        'limitations':[
            'A distinct publisher domain does not prove editorial or upstream data independence.',
            'Eight matches corroborate the observed slate, not that no games are omitted.',
            'Current capture timestamps do not establish 2023 publication or pregame availability.',
            'The listing is not an authoritative NBA schedule certification.'
        ],
        'next_evidence':'Review dated authoritative complete-slate publication and contemporaneous archival provenance separately; do not infer as-of eligibility.'
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project-root',required=True)
    ap.add_argument('--intake-review',required=True,help='S8.22.7.12 archived review.json')
    ap.add_argument('--governance-report',required=True,help='Exact S8.22.7.10 report referenced by intake')
    args=ap.parse_args()
    root=Path(args.project_root).resolve()
    intake_path=Path(args.intake_review).resolve()
    source=intake_path.parent/'source.bin'
    if not source.is_file(): ap.error('source.bin missing alongside intake review')
    if not intake_path.is_relative_to(root) or not source.is_relative_to(root): ap.error('intake must be inside project')
    if intake_path.parent.parent.name!=EXPECTED_DATE or intake_path.parent.parent.parent.name!='evidence' or intake_path.parent.parent.parent.parent.name!='s8_22_7_12': ap.error('unexpected evidence path')
    govpath=Path(args.governance_report).resolve()
    raw=source.read_bytes(); ib=intake_path.read_bytes(); gb=govpath.read_bytes()
    result=review(raw,json.loads(ib),json.loads(gb),ib,gb)
    output=root/'research/p0_s8/s8_22_7_13/results'/EXPECTED_DATE
    output.mkdir(parents=True,exist_ok=True)
    destination=output/('source_governance_'+uuid4().hex+'.json')
    destination.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',destination)
    print('STATUS:',result['status'])
    print('ISSUES:',result['issues'])
    print('DATE COMPLETENESS:',result['retrospective_date_completeness'])
    print('HISTORICAL AS-OF:',result['historical_asof'])
    print('DECISION:',result['decision'])
    if result['issues']: raise SystemExit(2)

if __name__=='__main__': main()
