"""Offline, fail-closed independent schedule completeness evidence assessment."""
import argparse
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

DATE = '2023-11-15'
EXPECTED = 'https://www.nba.com/games?date=2023-11-15'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def file_under(root, value):
    path = Path(value)
    path = (path if path.is_absolute() else root / path).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('Missing or out-of-project evidence file: ' + str(value))
    return path


def read(root, value):
    return json.loads(file_under(root, value).read_text(encoding='utf-8'))


def assess(root, governance_report, independent_manifest=None, independent_receipt=None):
    root = Path(root).resolve()
    prior = read(root, governance_report)
    checks, issues = {}, []

    def check(name, condition, detail=''):
        checks[name] = {'status': 'PASS' if condition else 'BLOCKED', 'detail': detail}
        if not condition:
            issues.append(name + (': ' + detail if detail else ''))

    check('prior_milestone', prior.get('milestone') == 'S8.22.7.10' and prior.get('date') == DATE)
    check('prior_game_agreement', prior.get('game_agreement') == 'PASS' and len(prior.get('reconstructed_matches', [])) == 8 and not prior.get('issues'))
    check('prior_governance', prior.get('decision') == 'BLOCK_TRAINING' and prior.get('date_completeness') == 'NOT_CERTIFIED')
    known = prior.get('reconstructed_matches', [])
    known_ids = [str(g.get('official_nba_game_id', '')) for g in known]
    check('prior_unique_game_ids', len(known_ids) == len(set(known_ids)) == 8)
    candidate = False
    provenance = {}
    if bool(independent_manifest) != bool(independent_receipt):
        check('independent_inputs_paired', False, 'Supply both manifest and receipt or neither')
    elif independent_manifest:
        manifest = read(root, independent_manifest)
        receipt = read(root, independent_receipt)
        path = file_under(root, receipt.get('evidence_path', ''))
        check('independent_source_integrity', digest(path) == receipt.get('sha256') and path.stat().st_size == receipt.get('bytes'))
        check('independent_manifest_date', manifest.get('date') == DATE and receipt.get('date') == DATE)
        check('independent_manifest_receipt_link', manifest.get('source_sha256') == receipt.get('sha256') and manifest.get('source_url') == receipt.get('source_url'))
        check('independent_origin', bool(manifest.get('source_url')) and manifest.get('source_url') != EXPECTED and manifest.get('source_url') != 'https://api.balldontlie.io/v1/games?dates%5B%5D=2023-11-15&per_page=100', 'Different URL alone is not proof of editorial independence')
        source_games = manifest.get('official_nba_game_ids')
        check('independent_games_explicit', isinstance(source_games, list) and len(source_games) == len(set(map(str, source_games))) == 8 and set(map(str, source_games)) == set(known_ids), 'Manifest must list all eight official game IDs')
        check('independent_exhaustiveness_claim', manifest.get('source_explicitly_states_full_date_slate') is True and isinstance(manifest.get('supporting_quote_or_locator'), str) and bool(manifest['supporting_quote_or_locator'].strip()), 'Requires human-reviewed locator in archived source; not machine-certified')
        check('independent_review_attribution', bool(manifest.get('reviewed_by')) and manifest.get('reviewed_by') != 'AUTO', 'Human attribution required')
        provenance = {'source_url': receipt.get('source_url'), 'source_sha256': receipt.get('sha256'), 'retrieved_utc': receipt.get('retrieved_utc')}
        candidate = not issues
    else:
        checks['independent_source'] = {'status': 'REVIEW_REQUIRED', 'detail': 'No separate archived authoritative full-date source and review manifest supplied'}
    return {
        'milestone': 'S8.22.7.11', 'date': DATE,
        'mode': 'OFFLINE_INDEPENDENT_COMPLETENESS_EVIDENCE_REVIEW',
        'prior_governance_report_sha256': digest(file_under(root, governance_report)),
        'checks': checks, 'issues': issues, 'independent_provenance': provenance,
        'game_agreement': 'PASS' if all(checks.get(k, {}).get('status') == 'PASS' for k in ('prior_milestone','prior_game_agreement','prior_governance','prior_unique_game_ids')) else 'BLOCKED',
        'independent_completeness_evidence': 'CANDIDATE_HUMAN_REVIEW_REQUIRED' if candidate else 'NOT_ESTABLISHED',
        'date_completeness': 'NOT_CERTIFIED',
        'historical_asof': 'NOT_CERTIFIED',
        'routine_collection_approved': False, 'training_eligible': False,
        'decision': 'BLOCK_TRAINING',
        'next_evidence': 'Human-reviewed independent authoritative full-date schedule proof, publication provenance, and historical pregame availability evidence',
        'limitations': ['No automated promotion to completeness certification', 'Retrospective snapshots do not establish historical as-of', 'Manifest declarations require manual source-content verification']
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--project-root', default='.')
    p.add_argument('--governance-report', required=True)
    p.add_argument('--independent-manifest')
    p.add_argument('--independent-receipt')
    a = p.parse_args()
    root = Path(a.project_root).resolve()
    result = assess(root, a.governance_report, a.independent_manifest, a.independent_receipt)
    out = root / 'research/p0_s8/s8_22_7_11/results/2023-11-15'
    out.mkdir(parents=True, exist_ok=True)
    target = out / ('independent_completeness_review_' + uuid.uuid4().hex + '.json')
    target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('REPORT:', target)
    print('GAME AGREEMENT:', result['game_agreement'])
    print('INDEPENDENT EVIDENCE:', result['independent_completeness_evidence'])
    print('DATE COMPLETENESS:', result['date_completeness'])
    print('DECISION:', result['decision'])
    print('ISSUES:', len(result['issues']))


if __name__ == '__main__':
    main()
