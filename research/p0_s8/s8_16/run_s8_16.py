"""S8.16 conservative artifact acquisition and independently timestamped capture audit.
No model training, no automatic pregame certification. Python stdlib only.
"""
import argparse
import csv
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

GAME = '0022300061'
TIPOFF = datetime.fromisoformat('2023-10-24T19:30:00-04:00')
OFFICIAL = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_2023-10-24_05PM.pdf'
CDX = 'https://web.archive.org/cdx/search/cdx?url=' + urllib.parse.quote(OFFICIAL, safe='') + '&output=json&filter=statuscode:200&collapse=timestamp:14'
HEADERS = {'User-Agent': 'NBA-MIKE-research-evidence-audit/1.0'}
MAX_BYTES = 15_000_000


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def fetch(url, target, timeout=20, max_bytes=MAX_BYTES):
    """Download only fixed approved HTTPS hosts, bound size; never overwrite a preserved artifact."""
    host = urllib.parse.urlparse(url)
    if host.scheme != 'https' or host.hostname not in {'ak-static.cms.nba.com', 'web.archive.org'}:
        raise ValueError('DISALLOWED_SOURCE_HOST')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError('PRESERVED_ARTIFACT_ALREADY_EXISTS')
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if urllib.parse.urlparse(response.geturl()).hostname not in {'ak-static.cms.nba.com', 'web.archive.org'}:
            raise ValueError('UNAPPROVED_REDIRECT')
        if response.status != 200:
            raise ValueError('HTTP_NOT_200')
        raw = response.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise ValueError('OVERSIZED_RESPONSE')
        metadata = {'requested_url': url, 'response_url': response.geturl(), 'http_status': response.status,
                    'date_header': response.headers.get('Date', ''), 'last_modified': response.headers.get('Last-Modified', ''),
                    'content_type': response.headers.get('Content-Type', ''), 'etag': response.headers.get('ETag', '')}
    # Exclusive creation, not a rename over a pre-existing evidence artifact.
    with target.open('xb') as f:
        f.write(raw)
    metadata.update(bytes=len(raw), sha256=sha256(target), acquired_utc=datetime.now(timezone.utc).isoformat())
    return metadata


def parse_cdx(path):
    if not path.is_file():
        return [], 'CDX_RESPONSE_MISSING'
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(raw, list) or not raw or not isinstance(raw[0], list):
            return [], 'CDX_SCHEMA_INVALID'
        header = raw[0]
        if 'timestamp' not in header or 'original' not in header:
            return [], 'CDX_REQUIRED_COLUMNS_MISSING'
        items = [dict(zip(header, row)) for row in raw[1:] if isinstance(row, list) and len(row) == len(header)]
        return items, ''
    except (ValueError, UnicodeError, OSError):
        return [], 'CDX_PARSE_FAILED'


def archive_review(items):
    rows = []
    for item in items:
        ts = str(item.get('timestamp', ''))
        url = str(item.get('original', ''))
        if not re.fullmatch(r'\d{14}', ts):
            verdict, reason = 'REJECTED', 'INVALID_ARCHIVE_TIMESTAMP'
        elif url != OFFICIAL:
            verdict, reason = 'REJECTED', 'ARCHIVE_ORIGINAL_URL_MISMATCH'
        else:
            dt = datetime.strptime(ts, '%Y%m%d%H%M%S').replace(tzinfo=timezone.utc)
            verdict, reason = ('CANDIDATE_PRE_TIPOFF_CAPTURE', 'ARCHIVE_INDEX_NOT_INDEPENDENTLY_VALIDATED') if dt < TIPOFF else ('POST_TIPOFF', 'ARCHIVE_CAPTURE_NOT_PRE_TIPOFF')
        rows.append({'archive_timestamp_utc': ts, 'original_url': url, 'archive_url': f'https://web.archive.org/web/{ts}id_/{OFFICIAL}' if re.fullmatch(r'\d{14}', ts) else '', 'index_verdict': verdict, 'reason': reason})
    return rows


def pdf_metadata(path):
    if not path.is_file():
        return {'pdf_present': False, 'pdf_signature_valid': False, 'creation_date_claim': '', 'mod_date_claim': ''}
    data = path.read_bytes()
    valid = data.startswith(b'%PDF-')
    def match(key):
        m = re.search(rb'/' + key + rb'\s*\(([^)]{0,100})\)', data)
        return m.group(1).decode('latin-1', errors='replace') if m else ''
    return {'pdf_present': True, 'pdf_signature_valid': valid, 'creation_date_claim': match(b'CreationDate'), 'mod_date_claim': match(b'ModDate')}


def audit(root, acquire=False, acquire_archive=False):
    base = root / 'research/p0_s8/s8_16'
    art = base / 'artifacts'
    results = base / 'results'
    art.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    acquisition = []
    tasks = [(OFFICIAL, art / 'official_2023_10_24_05PM.pdf', 'official_pdf')]
    if acquire_archive:
        tasks.append((CDX, art / 'wayback_cdx_response.json', 'wayback_cdx'))
    if acquire or acquire_archive:
        for url, dest, label in tasks:
            if label == 'official_pdf' and not acquire:
                continue
            try:
                meta = fetch(url, dest)
                acquisition.append({'source': label, 'status': 'ACQUIRED', **meta})
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
                acquisition.append({'source': label, 'status': 'FAILED_OR_ALREADY_PRESENT', 'error': type(exc).__name__ + ': ' + str(exc)[:240]})
    pdf = art / 'official_2023_10_24_05PM.pdf'
    archive = art / 'wayback_cdx_response.json'
    pdf_info = pdf_metadata(pdf)
    items, cdx_error = parse_cdx(archive)
    captures = archive_review(items)
    with (results / 's8_16_archive_candidates.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['archive_timestamp_utc', 'original_url', 'archive_url', 'index_verdict', 'reason'])
        writer.writeheader(); writer.writerows(captures)
    manifest = []
    for path, label in [(pdf, 'official_pdf'), (archive, 'wayback_cdx')]:
        if path.is_file():
            manifest.append({'source': label, 'relative_path': str(path.relative_to(root)), 'sha256': sha256(path), 'bytes': path.stat().st_size, 'evidence_type': 'CURRENT_RETRIEVAL_NOT_HISTORICAL_PROOF'})
    with (results / 's8_16_artifact_manifest.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['source', 'relative_path', 'sha256', 'bytes', 'evidence_type'])
        writer.writeheader(); writer.writerows(manifest)
    report = {'milestone': 'S8.16', 'mode': 'OFFICIAL_ARTIFACT_ACQUISITION_AND_ARCHIVE_INDEX_AUDIT',
              'game_id': GAME, 'scheduled_tipoff_et': TIPOFF.isoformat(), 'official_pdf_url': OFFICIAL,
              'network_opt_in': bool(acquire or acquire_archive), 'acquisition_attempts': acquisition,
              'artifacts_preserved': len(manifest), 'pdf_inspection': pdf_info, 'cdx_parse_issue': cdx_error,
              'archive_rows': len(captures), 'archive_pre_tipoff_candidates': sum(r['index_verdict'] == 'CANDIDATE_PRE_TIPOFF_CAPTURE' for r in captures),
              'independently_verified_publication': False, 'independently_verified_games': 0,
              'verdict': 'UNVERIFIED', 'decision': 'BLOCK_TRAINING', 'status': 'RESEARCH_ONLY',
              'limitations': ['A current official PDF download does not prove historical public availability',
                              'PDF internal CreationDate/ModDate and HTTP Date/Last-Modified are not independent historical proof',
                              'CDX index entries are discovery candidates; original archive replay, identity, timestamp and capture integrity require independent review',
                              'Injury reports do not establish complete pregame player population or DNP reconciliation',
                              '88 restart-period games remain separately blocked']}
    (results / 's8_16_report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root', default='.')
    p.add_argument('--acquire-official', action='store_true', help='Opt in to live NBA PDF retrieval')
    p.add_argument('--query-wayback', action='store_true', help='Opt in to Wayback CDX index retrieval')
    a = p.parse_args()
    print(json.dumps(audit(Path(a.project_root).resolve(), a.acquire_official, a.query_wayback), indent=2))

if __name__ == '__main__':
    main()
