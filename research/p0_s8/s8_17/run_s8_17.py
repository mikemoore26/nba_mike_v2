"""S8.17: bounded historical archive diagnostics; discovery only, never certifies training."""
import argparse
import csv
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OFFICIAL = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_2023-10-24_05PM.pdf'
TIPOFF = datetime.fromisoformat('2023-10-24T19:30:00-04:00')
HEADERS = {'User-Agent': 'NBA-MIKE-research-audit/1.0'}
MAX_BYTES = 2_000_000


def parse_cdx_bytes(blob):
    try:
        data = json.loads(blob.decode('utf-8-sig'))
    except (UnicodeError, ValueError):
        return [], 'MALFORMED_JSON'
    if data == []:
        return [], 'VALID_EMPTY_CDX_ARRAY'
    if not isinstance(data, list) or not data or not isinstance(data[0], list):
        return [], 'UNEXPECTED_CDX_SCHEMA'
    header = data[0]
    if not {'timestamp', 'original'}.issubset(set(header)):
        return [], 'CDX_REQUIRED_COLUMNS_MISSING'
    return [dict(zip(header, row)) for row in data[1:] if isinstance(row, list) and len(row) == len(header)], 'PARSED'


def classify(item):
    ts = str(item.get('timestamp', ''))
    original = str(item.get('original', ''))
    if len(ts) != 14 or not ts.isdigit() or original != OFFICIAL:
        return 'REJECTED'
    try:
        captured = datetime.strptime(ts, '%Y%m%d%H%M%S').replace(tzinfo=timezone.utc)
    except ValueError:
        return 'REJECTED'
    return 'CANDIDATE_PRE_TIPOFF_CAPTURE' if captured < TIPOFF else 'POST_TIPOFF'


def endpoints():
    encoded = urllib.parse.quote(OFFICIAL, safe='')
    return [
        ('cdx_json_exact', 'https://web.archive.org/cdx/search/cdx?url=' + encoded + '&output=json&filter=statuscode:200'),
        ('cdx_json_all_status', 'https://web.archive.org/cdx/search/cdx?url=' + encoded + '&output=json'),
        ('cdx_text_exact', 'https://web.archive.org/cdx/search/cdx?url=' + encoded + '&output=txt&fl=timestamp,original,statuscode'),
        ('availability_api', 'https://archive.org/wayback/available?url=' + encoded + '&timestamp=20231024'),
    ]


def retrieve(url, target, timeout=12):
    if target.exists():
        return {'status': 'PRESERVED_EXISTING', 'bytes': target.stat().st_size, 'sha256': digest(target)}
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        resolved = urllib.parse.urlparse(response.geturl())
        if resolved.scheme != 'https' or resolved.hostname not in {'web.archive.org', 'archive.org'}:
            raise ValueError('DISALLOWED_REDIRECT')
        if response.status != 200:
            raise ValueError('HTTP_NOT_200')
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError('RESPONSE_TOO_LARGE')
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
        return {'status': 'ACQUIRED', 'bytes': len(data), 'sha256': digest(target), 'response_url': response.geturl(), 'content_type': response.headers.get('Content-Type', '')}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path, fields, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def run(root, network=False):
    base = root / 'research/p0_s8/s8_17'
    artifacts = base / 'artifacts'
    results = base / 'results'
    results.mkdir(parents=True, exist_ok=True)
    previous = root / 'research/p0_s8/s8_16/artifacts'
    prior_candidates = list(previous.rglob('*.json')) if previous.exists() else []
    audit = []
    candidates = []
    for name, url in endpoints():
        path = artifacts / (name + ('.txt' if 'text' in name else '.json'))
        record = {'source': name, 'url': url, 'artifact_path': str(path.relative_to(root)), 'status': 'NOT_REQUESTED', 'parse_status': '', 'rows': 0, 'sha256': '', 'bytes': 0, 'error': ''}
        if network:
            try:
                record.update(retrieve(url, path))
            except Exception as exc:
                record.update(status='REQUEST_FAILED', error=f'{type(exc).__name__}: {str(exc)[:240]}')
        if path.exists():
            record['sha256'] = digest(path)
            record['bytes'] = path.stat().st_size
            if name.startswith('cdx_json'):
                items, status = parse_cdx_bytes(path.read_bytes())
                record['parse_status'] = status
                record['rows'] = len(items)
                for item in items:
                    candidates.append({'source': name, 'timestamp': item.get('timestamp', ''), 'original': item.get('original', ''), 'index_verdict': classify(item), 'independently_verified': 'NO'})
            elif name == 'cdx_text_exact':
                lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
                record['parse_status'] = 'TEXT_ONLY_REVIEW_REQUIRED' if lines else 'EMPTY_TEXT_RESPONSE'
                record['rows'] = max(0, len(lines) - 1)
            else:
                try:
                    data = json.loads(path.read_text(encoding='utf-8'))
                    record['parse_status'] = 'AVAILABILITY_JSON_OBJECT' if isinstance(data, dict) else 'AVAILABILITY_UNEXPECTED_SCHEMA'
                except (OSError, ValueError):
                    record['parse_status'] = 'AVAILABILITY_PARSE_FAILED'
        audit.append(record)
    # Reclassify the 3-byte S8.16 [] response if present; do not modify source evidence.
    prior = []
    for path in prior_candidates:
        if path.is_file() and path.stat().st_size <= MAX_BYTES:
            items, status = parse_cdx_bytes(path.read_bytes())
            prior.append({'path': str(path.relative_to(root)), 'sha256': digest(path), 'cdx_parse_status': status, 'rows': len(items)})
    write_csv(results / 's8_17_request_audit.csv', ['source', 'url', 'artifact_path', 'status', 'parse_status', 'rows', 'sha256', 'bytes', 'error'], audit)
    write_csv(results / 's8_17_capture_candidates.csv', ['source', 'timestamp', 'original', 'index_verdict', 'independently_verified'], candidates)
    report = {'milestone': 'S8.17', 'mode': 'BOUNDED_ARCHIVE_DIAGNOSTIC', 'status': 'RESEARCH_ONLY', 'decision': 'BLOCK_TRAINING', 'network_opt_in': network, 'sources_attempted': sum(a['status'] != 'NOT_REQUESTED' for a in audit), 'sources_acquired_or_preserved': sum(a['status'] in ('ACQUIRED', 'PRESERVED_EXISTING') for a in audit), 'archive_index_candidates': len(candidates), 'independently_verified_publication': False, 'independently_verified_games': 0, 'previous_s816_json_artifacts': prior, 'requests': audit, 'conclusion': 'ARCHIVE_INDEX_DISCOVERY_ONLY_NO_CERTIFICATION', 'limitations': ['CDX [] is a valid empty response, not a malformed schema', 'Index and availability API claims are not independently verified captures', 'Archive replay bytes and timestamp integrity not established', 'Injury report does not establish complete pregame eligible player population', 'No training or models executed; 88 restart games remain unresolved']}
    (results / 's8_17_report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', type=Path, default=Path('.'))
    parser.add_argument('--query-archives', action='store_true', help='Explicitly enable bounded archive network requests')
    args = parser.parse_args()
    result = run(args.project_root.resolve(), args.query_archives)
    print(json.dumps({'decision': result['decision'], 'sources_attempted': result['sources_attempted'], 'archive_index_candidates': result['archive_index_candidates']}, indent=2))
