"""S8.22.2 offline source governance comparison; zero network calls."""
from __future__ import annotations
import argparse, csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

SOURCES = [
    dict(source_id='NBA_CDN_S822', provider='NBA', source_kind='OFFICIAL_UNDOCUMENTED_CDN', access_evidence='LOCAL_HTTP_403_2026_10_09', authorization='UNVERIFIED', schema='S8_22_PARSER_NOT_LIVE_VALIDATED', id_policy='NBA_ID_EXPECTED_UNVERIFIED', timestamp_policy='UTC_VALIDATION_REQUIRED', cost='UNKNOWN', recommendation='BLOCKED_DO_NOT_RETRY'),
    dict(source_id='ESPN_SITE_SCOREBOARD', provider='ESPN', source_kind='UNOFFICIAL_UNDOCUMENTED_SITE_API', access_evidence='THIRD_PARTY_DOCUMENTATION_ONLY', authorization='UNVERIFIED', schema='UNVERIFIED_LOCALLY', id_policy='ESPN_IDS_REQUIRE_EXPLICIT_CROSSWALK', timestamp_policy='UTC_VALIDATION_REQUIRED', cost='NO_KEY_REPORTED_NOT_LICENSE', recommendation='RESEARCH_ONLY_NO_LIVE_COLLECTION'),
    dict(source_id='BALLDONTLIE', provider='balldontlie', source_kind='DOCUMENTED_PROVIDER_CANDIDATE', access_evidence='NOT_TESTED', authorization='TERMS_AND_PLAN_REVIEW_REQUIRED', schema='NOT_TESTED', id_policy='PROVIDER_IDS_REQUIRE_CROSSWALK', timestamp_policy='UTC_VALIDATION_REQUIRED', cost='PLAN_AND_COVERAGE_UNVERIFIED', recommendation='SHORTLIST_FOR_TERMS_REVIEW'),
    dict(source_id='SPORTSRADAR', provider='Sportradar', source_kind='LICENSED_PROVIDER_CANDIDATE', access_evidence='NOT_TESTED', authorization='CONTRACT_AND_PLAN_REQUIRED', schema='NOT_TESTED', id_policy='PROVIDER_IDS_REQUIRE_CROSSWALK', timestamp_policy='UTC_VALIDATION_REQUIRED', cost='COMMERCIAL_PLAN_UNVERIFIED', recommendation='SHORTLIST_IF_BUDGET_PERMITS'),
    dict(source_id='API_SPORTS', provider='API-Sports', source_kind='DOCUMENTED_PROVIDER_CANDIDATE', access_evidence='NOT_TESTED', authorization='TERMS_AND_PLAN_REVIEW_REQUIRED', schema='NOT_TESTED', id_policy='PROVIDER_IDS_REQUIRE_CROSSWALK', timestamp_policy='UTC_VALIDATION_REQUIRED', cost='PLAN_AND_COVERAGE_UNVERIFIED', recommendation='SHORTLIST_FOR_TERMS_REVIEW'),
]
FIELDS = list(SOURCES[0])

def evaluate(root: Path) -> dict:
    root = root.resolve()
    results = root / 'research/p0_s8/s8_22_2/results'
    results.mkdir(parents=True, exist_ok=True)
    inventory = root / 'research/p0_s8/s8_22/results/s8_22_report.json'
    prior = {'path': str(inventory.relative_to(root)), 'exists': inventory.is_file(), 'sha256': None, 'reported_http_status': None, 'read_status': 'NOT_FOUND'}
    if inventory.is_file():
        blob = inventory.read_bytes()
        prior['sha256'] = hashlib.sha256(blob).hexdigest()
        try:
            doc = json.loads(blob)
            prior['reported_http_status'] = doc.get('http_status') or (doc.get('http_error_diagnostics') or {}).get('http_status')
            prior['read_status'] = 'PARSED'
        except (ValueError, UnicodeError, TypeError):
            prior['read_status'] = 'UNPARSEABLE'
    with (results / 's8_22_2_source_matrix.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS); writer.writeheader(); writer.writerows(SOURCES)
    gates = [
        ('PERMISSION','Written terms/license or provider confirmation covering automated research capture'),
        ('REACHABILITY','Single authorized manual retrieval with bounded timeout and no restriction bypass'),
        ('SCHEMA','Real response schema, required game fields, and malformed-data tests'),
        ('COVERAGE','Upcoming game completeness across several dates and season boundaries'),
        ('IDENTIFIERS','Source-specific game IDs plus explicit verified crosswalk to canonical IDs'),
        ('TIPOFF','Timezone-aware scheduled tipoff, updates, postponements and DST'),
        ('PROVENANCE','S8.21 raw bytes, receipt UTC, HTTP headers, checksum, failures'),
        ('ELIGIBILITY','Independent game-specific pregame player universe, separately gated'),
    ]
    with (results / 's8_22_2_acceptance_gates.csv').open('w', newline='', encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['gate','requirement','status']); w.writerows((a,b,'NOT_SATISFIED') for a,b in gates)
    report = dict(milestone='S8.22.2', generated_utc=datetime.now(timezone.utc).isoformat(), mode='OFFLINE_SOURCE_COMPARISON', sources_evaluated=len(SOURCES), network_requests=0, model_fits=0, prior_s822_report=prior, preferred_next_action='VERIFY_DOCUMENTED_PROVIDER_TERMS_AND_COVERAGE_BEFORE_ANY_LIVE_ADAPTER', espn_assessment='UNOFFICIAL_ACCESS_NOT_PERMISSION', nba_cdn='BLOCKED_AFTER_HTTP_403', approved_live_sources=[], gates_satisfied=0, total_gates=len(gates), status='RESEARCH_ONLY', decision='BLOCK_TRAINING', verdict='SOURCE_SELECTION_PENDING_AUTHORIZATION_AND_LIVE_VALIDATION', limitations=['No live endpoint contacted','Provider plan terms, costs and game coverage not independently verified','No game IDs or tipoff timestamps verified','No pregame player eligibility certified','88 restart games separately blocked'])
    (results/'s8_22_2_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--project-root',default='.'); args=p.parse_args()
    print(json.dumps(evaluate(Path(args.project_root)),indent=2))
