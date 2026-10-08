"""S7.1 official injury report version registry; no PDF scraping or model training."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import urlparse
import csv, hashlib, json, re

HOST = 'ak-static.cms.nba.com'
NAME = re.compile(r'^Injury-Report_(\d{4}-\d{2}-\d{2})_(\d{1,2})(?:_(\d{2}))?(AM|PM)\.pdf$', re.I)
ET = ZoneInfo('America/New_York')

def parse_official_url(url: str) -> dict:
    p = urlparse(url)
    if p.scheme != 'https' or p.netloc != HOST or not p.path.startswith('/referee/injury/') or p.query or p.fragment:
        raise ValueError('not an exact official NBA injury-report PDF URL')
    m = NAME.fullmatch(Path(p.path).name)
    if not m:
        raise ValueError('unrecognized official report filename')
    date, hour, minute, ampm = m.groups()
    hour = int(hour)
    if not 1 <= hour <= 12:
        raise ValueError('invalid 12-hour clock')
    dt = datetime.strptime(date, '%Y-%m-%d').replace(hour=(hour % 12) + (12 if ampm.upper() == 'PM' else 0), minute=int(minute or 0), tzinfo=ET)
    return {'url': url, 'report_time_et': dt.isoformat(), 'report_time_utc': dt.astimezone(timezone.utc).isoformat()}

def verify_pdf_bytes(data: bytes) -> str:
    if not data.startswith(b'%PDF-'):
        raise ValueError('not a PDF header')
    return hashlib.sha256(data).hexdigest()

def select_asof(versions: list[dict], cutoff_utc: str) -> dict | None:
    cutoff = _aware(cutoff_utc)
    eligible = []
    for v in versions:
        if not v.get('sha256') or not re.fullmatch('[0-9a-f]{64}', str(v['sha256'])):
            continue
        parsed = parse_official_url(v['url'])
        published = _aware(v.get('published_at_utc', parsed['report_time_utc']))
        obtained = _aware(v['available_at_utc'])
        if obtained < published:
            raise ValueError('available_at precedes published_at')
        if published <= cutoff and obtained <= cutoff:
            eligible.append((published, obtained, v))
    return max(eligible, key=lambda x: (x[0], x[1]))[2] if eligible else None

def _aware(value: str) -> datetime:
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None or d.utcoffset() is None:
        raise ValueError('timezone offset required')
    return d.astimezone(timezone.utc)

def audit_registry(rows: list[dict]) -> dict:
    results=[]
    for r in rows:
        try:
            parsed = parse_official_url(r['url'])
            sha = r.get('sha256','')
            if sha and not re.fullmatch('[0-9a-f]{64}', sha):
                raise ValueError('invalid sha256')
            available = r.get('available_at_utc','')
            if available:
                if _aware(available) < _aware(r.get('published_at_utc') or parsed['report_time_utc']):
                    raise ValueError('available_at precedes published_at')
            results.append({'url':r['url'],'status':'PROVENANCE_COMPLETE' if sha and available else 'SOURCE_REFERENCE_ONLY', **parsed})
        except (ValueError,KeyError) as exc:
            results.append({'url':r.get('url',''), 'status':'REJECTED', 'reason':str(exc)})
    return {'status':'AUDIT_ONLY_NO_MODEL_PROMOTION','count':len(rows),'records':results,'verified_for_historical_asof':sum(x['status']=='PROVENANCE_COMPLETE' for x in results),'warning':'Report filename time is not independent proof of public availability; availability timestamps require evidence.'}
