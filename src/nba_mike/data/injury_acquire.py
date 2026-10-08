"""S7.15 allowlisted official NBA PDF acquisition. Research-only; no as-of claims."""
from __future__ import annotations
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

HOST = 'ak-static.cms.nba.com'
PATH_RE = re.compile(r'^/referee/injury/Injury-Report_\d{4}-\d{2}-\d{2}_\d{2}_\d{2}(?:AM|PM)\.pdf$')
MAX_BYTES = 12 * 1024 * 1024


def validate_url(url):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname != HOST or parsed.port is not None or parsed.username or parsed.password or parsed.query or parsed.fragment or not PATH_RE.fullmatch(parsed.path):
        raise ValueError('URL must be an exact official NBA injury-report PDF URL on the allowlist')
    return url


def fetch_pdf(url, *, timeout=20, opener=None):
    validate_url(url)
    req = urllib.request.Request(url, headers={'User-Agent': 'NBA-MIKE-Research/1.0', 'Accept': 'application/pdf'})
    if opener is None:
        opener = urllib.request.urlopen
    with opener(req, timeout=timeout) as response:
        # urllib follows redirects; reject any redirect outside the allowlist.
        final_url = response.geturl()
        validate_url(final_url)
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('PDF exceeds maximum permitted size')
        if not raw.startswith(b'%PDF-') or b'%%EOF' not in raw[-2048:]:
            raise ValueError('Response is not a complete PDF')
        return raw, final_url


def acquire(urls, pdf_dir, result_dir, *, opener=None, timeout=20):
    pdf_dir = Path(pdf_dir); result_dir = Path(result_dir)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)
    if not urls or len(urls) > 12:
        raise ValueError('Supply 1 to 12 explicit URLs')
    if len(urls) != len(set(urls)):
        raise ValueError('Duplicate URLs in manifest')
    # Fail closed before any network requests.
    for url in urls:
        validate_url(url)
    existing = {}
    for path in pdf_dir.glob('*.pdf'):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        existing[digest] = str(path)
    entries = []
    for url in urls:
        row = {'requested_url': url, 'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
               'historical_publication_verified': False, 'eligible_for_asof_training': False}
        try:
            raw, final_url = fetch_pdf(url, opener=opener, timeout=timeout)
            sha = hashlib.sha256(raw).hexdigest()
            row.update(final_url=final_url, sha256=sha, size_bytes=len(raw))
            if sha in existing:
                row.update(status='DUPLICATE_BYTES', local_path=existing[sha])
            else:
                target = pdf_dir / f'{sha}.pdf'
                target.write_bytes(raw)
                existing[sha] = str(target)
                row.update(status='DOWNLOADED', local_path=str(target))
        except Exception as exc:
            row.update(status='FETCH_FAILED', error=f'{type(exc).__name__}: {exc}'[:300])
        entries.append(row)
    summary = {'status': 'RESEARCH_ONLY', 'decision': 'BLOCK_TRAINING',
               'attempted': len(entries), 'downloaded': sum(x['status']=='DOWNLOADED' for x in entries),
               'duplicates': sum(x['status']=='DUPLICATE_BYTES' for x in entries),
               'failed': sum(x['status']=='FETCH_FAILED' for x in entries),
               'historical_publication_verified': False, 'eligible_for_asof_training': False,
               'entries': entries,
               'limitations': ['Official-domain retrieval is not independent proof of historical publication time',
                               'Filename time is not historical availability evidence',
                               'PDF content and extracted player rows still require independent validation']}
    (result_dir/'s7_15_acquisition.json').write_text(json.dumps(summary,indent=2)+'\n', encoding='utf-8')
    return summary
