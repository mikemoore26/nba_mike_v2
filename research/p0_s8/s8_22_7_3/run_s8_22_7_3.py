"""S8.22.7.3: multi-source NBA game reference, independent per-row provenance.

Offline only. No claims of complete-date schedule or historical as-of availability.
"""
import argparse
import csv
import hashlib
from html.parser import HTMLParser
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import uuid
from urllib.parse import urlsplit

FIELDS = ['game_date', 'official_nba_game_id', 'home_team', 'away_team', 'tipoff_utc', 'source_url', 'evidence_sha256', 'evidence_retrieved_utc']


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def nba_url(url):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in ('nba.com', 'www.nba.com') or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('NBA_OFFICIAL_HTTPS_REQUIRED')
    return parsed


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__(); self.inside = False; self.chunks = []; self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            attrs = dict(attrs)
            self.inside = attrs.get('type') == 'application/ld+json'
            self.chunks = []

    def handle_data(self, data):
        if self.inside: self.chunks.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.inside:
            self.scripts.append(''.join(self.chunks))
            self.inside = False


def sports_events(obj):
    if isinstance(obj, list):
        for item in obj: yield from sports_events(item)
    elif isinstance(obj, dict):
        if obj.get('@type') == 'SportsEvent' or (isinstance(obj.get('@type'), list) and 'SportsEvent' in obj['@type']):
            yield obj
        for value in obj.values():
            if isinstance(value, (dict, list)): yield from sports_events(value)


def parse_game(html, url, game_date):
    nba_url(url)
    page = Scripts(); page.feed(html.decode('utf-8', errors='replace'))
    events = []
    for script in page.scripts:
        try: events.extend(sports_events(json.loads(script)))
        except json.JSONDecodeError: continue
    if not events: raise ValueError('OFFICIAL_STRUCTURED_GAME_MISSING')
    parsed = nba_url(url)
    game_id = re.search(r'(00\d{8})(?:/)?$', parsed.path)
    if not game_id: raise ValueError('OFFICIAL_GAME_ID_MISSING_IN_URL')
    candidates = []
    for event in events:
        try:
            home = event['homeTeam']['alternateName'].strip().upper()
            away = event['awayTeam']['alternateName'].strip().upper()
            start = datetime.fromisoformat(event['startDate'].replace('Z', '+00:00'))
        except (KeyError, TypeError, ValueError, AttributeError): continue
        if start.tzinfo is None or not re.fullmatch('[A-Z]{2,3}', home) or not re.fullmatch('[A-Z]{2,3}', away) or home == away:
            continue
        # NBA game date is local Eastern date, not UTC calendar date.
        from zoneinfo import ZoneInfo
        if start.astimezone(ZoneInfo('America/New_York')).date().isoformat() != game_date: continue
        candidates.append((home, away, start.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')))
    if len(set(candidates)) != 1: raise ValueError('STRUCTURED_GAME_MISSING_OR_AMBIGUOUS')
    home, away, tipoff = candidates[0]
    # Avoid trusting an arbitrary JSON-LD SportsEvent that doesn't match canonical NBA game path.
    if not re.search(rf'<link\s+[^>]*rel="canonical"[^>]*href="{re.escape(url)}"', html.decode('utf-8', errors='replace')):
        raise ValueError('CANONICAL_GAME_URL_MISMATCH')
    return dict(game_date=game_date, official_nba_game_id=game_id.group(1), home_team=home, away_team=away, tipoff_utc=tipoff)


def checked_receipt(root, receipt_path, game_date):
    root = root.resolve(); receipt_path = Path(receipt_path).resolve()
    if not receipt_path.is_relative_to(root): raise ValueError('RECEIPT_OUTSIDE_PROJECT')
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    if receipt.get('date') != game_date: raise ValueError('RECEIPT_DATE_MISMATCH')
    nba_url(receipt['source_url'])
    evidence_rel = Path(receipt['evidence_path'])
    if evidence_rel.is_absolute() or '..' in evidence_rel.parts: raise ValueError('UNSAFE_EVIDENCE_PATH')
    evidence = (root/evidence_rel).resolve()
    if not evidence.is_relative_to(root) or not evidence.is_file(): raise ValueError('EVIDENCE_NOT_FOUND')
    content = evidence.read_bytes()
    if len(content) != receipt['bytes'] or digest(content) != receipt['sha256']:
        raise ValueError('EVIDENCE_HASH_MISMATCH')
    dt = datetime.fromisoformat(receipt['retrieved_utc'].replace('Z', '+00:00'))
    if dt.tzinfo is None: raise ValueError('RECEIPT_TIME_NO_ZONE')
    return receipt, content


def build(root, game_date, receipts):
    root = Path(root).resolve()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', game_date): raise ValueError('INVALID_DATE')
    if not receipts: raise ValueError('NO_RECEIPTS')
    rows = []
    for path in receipts:
        receipt, content = checked_receipt(root, path, game_date)
        row = parse_game(content, receipt['source_url'], game_date)
        row.update(source_url=receipt['source_url'], evidence_sha256=receipt['sha256'], evidence_retrieved_utc=receipt['retrieved_utc'])
        rows.append(row)
    ids = [r['official_nba_game_id'] for r in rows]
    if len(ids) != len(set(ids)): raise ValueError('DUPLICATE_OFFICIAL_GAME_ID')
    rows.sort(key=lambda r: (r['tipoff_utc'], r['official_nba_game_id']))
    output_dir = root/'research/p0_s8/s8_22_7_3/results'/game_date
    output_dir.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    target = output_dir/f'official_reference_{token}.csv'
    with target.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
    report = dict(milestone='S8.22.7.3', date=game_date, reference_path=target.relative_to(root).as_posix(),
                  reference_sha256=digest(target.read_bytes()), official_games=len(rows),
                  official_game_ids=ids, source_receipts=len(receipts),
                  row_provenance_verified=True, date_completeness='NOT_CERTIFIED',
                  historical_asof='NOT_CERTIFIED', status='CANDIDATE_GAME_EVIDENCE_ONLY',
                  routine_collection_approved=False, training_eligible=False,
                  decision='BLOCK_TRAINING')
    report_path = output_dir/f'report_{token}.json'
    report_path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report



def provisional_compare(root, game_date, reference_path, provider_path, crosswalk_path):
    """Reuse existing S8.22.7 matching, without touching its manifest."""
    import importlib.util
    module_path = root/'research/p0_s8/s8_22_7/run_s8_22_7.py'
    spec = importlib.util.spec_from_file_location('nba_s8227_compare', module_path)
    if spec is None or spec.loader is None: raise ValueError('S8_22_7_RUNNER_MISSING')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    mapping = {}
    for row in module.read_csv(crosswalk_path, {'provider_team_id','official_team','evidence_url','reviewed_by'}):
        pid = row['provider_team_id'].strip()
        if not pid or pid in mapping or not row['evidence_url'].strip() or not row['reviewed_by'].strip():
            raise ValueError('CROSSWALK_INVALID')
        mapping[pid] = row['official_team'].strip().upper()
    result = module.audit_date(game_date, provider_path, root/reference_path, mapping)
    result['comparison_scope'] = 'SUPPLIED_GAME_EVIDENCE_ONLY_NOT_FULL_DATE'
    result['date_completeness'] = 'NOT_CERTIFIED'
    result['training_eligible'] = False
    result['decision'] = 'BLOCK_TRAINING'
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root', type=Path, default=Path('.'))
    p.add_argument('--date', required=True)
    p.add_argument('--receipt', action='append', required=True, type=Path, help='Repeat once per game; path within project')
    p.add_argument('--provider-csv', type=Path, help='Optional provider snapshot for provisional comparison')
    p.add_argument('--crosswalk', type=Path, help='Required with --provider-csv')
    a = p.parse_args()
    root = a.project_root.resolve()
    result = build(root, a.date, a.receipt)
    if a.provider_csv:
        if not a.crosswalk: p.error('--crosswalk required with --provider-csv')
        result['provisional_comparison'] = provisional_compare(root, a.date, result['reference_path'], a.provider_csv, a.crosswalk)
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
