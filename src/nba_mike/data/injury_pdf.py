"""S7.2 research-only official NBA injury PDF acquisition and conservative extraction.

Report filename time is NOT proof that the report was publicly available then.
"""
from __future__ import annotations
import hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from .injury_asof import parse_official_url, verify_pdf_bytes

MAX_BYTES = 12_000_000
STATUS = re.compile(r'\b(Out|Doubtful|Questionable|Probable|Available)\b', re.I)

def fetch_pdf(url: str, *, timeout: int = 20) -> bytes:
    parse_official_url(url)  # strict HTTPS host/path/filename allowlist
    req = Request(url, headers={'User-Agent': 'NBA-MIKE-research/0.1 (public injury reports)'})
    with urlopen(req, timeout=timeout) as response:
        final_url = response.geturl()
        parse_official_url(final_url)
        if final_url != url:
            raise ValueError('redirected URL differs from requested official report')
        content_type = response.headers.get('Content-Type', '').split(';')[0].strip().lower()
        if content_type not in ('application/pdf', 'application/octet-stream'):
            raise ValueError('unexpected content type')
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('PDF exceeds configured size limit')
    verify_pdf_bytes(data)
    return data

def extract_pdf_text(data: bytes) -> list[dict]:
    verify_pdf_bytes(data)
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError('PyMuPDF required: pip install pymupdf') from exc
    pages=[]
    with fitz.open(stream=data, filetype='pdf') as pdf:
        for i, page in enumerate(pdf, 1):
            text=page.get_text('text', sort=True)
            pages.append({'page':i, 'text':text, 'chars':len(text)})
    return pages

def conservative_candidates(pages: list[dict]) -> list[dict]:
    """Extract status-containing lines for human review; do NOT claim player-level records."""
    rows=[]
    for page in pages:
        for line_no, line in enumerate(page['text'].splitlines(), 1):
            m=STATUS.search(line)
            if m:
                rows.append({'page':page['page'], 'line':line_no, 'raw_text':line.strip(),
                             'status_token':m.group(1).upper(), 'review_status':'NEEDS_MANUAL_SCHEMA_VALIDATION'})
    return rows

def acquire_and_audit(url: str, output_dir: Path, *, data: bytes | None = None,
                      fetched_at_utc: str | None = None) -> dict:
    parsed=parse_official_url(url)
    data=fetch_pdf(url) if data is None else data
    sha=verify_pdf_bytes(data)
    if len(data)>MAX_BYTES: raise ValueError('PDF exceeds configured size limit')
    pages=extract_pdf_text(data)
    candidates=conservative_candidates(pages)
    observed=datetime.now(timezone.utc).isoformat() if fetched_at_utc is None else fetched_at_utc
    ts=datetime.fromisoformat(observed.replace('Z','+00:00'))
    if ts.tzinfo is None or ts.utcoffset() is None: raise ValueError('fetched_at_utc must be timezone-aware')
    output_dir=Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    name=sha+'.pdf'
    dest=output_dir/name
    if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()!=sha:
        raise ValueError('existing file hash mismatch')
    dest.write_bytes(data)
    result={'status':'QUARANTINED_RESEARCH_ONLY','url':url,
            'filename_report_time_utc':parsed['report_time_utc'],
            'downloaded_at_utc':ts.astimezone(timezone.utc).isoformat(),
            'sha256':sha,'bytes':len(data),'pdf_path':str(dest),
            'pages':len(pages),'text_chars':sum(p['chars'] for p in pages),
            'status_line_candidates':candidates,
            'historical_publication_verified':False,
            'eligible_for_asof_training':False,
            'limitations':['Filename time does not establish actual public availability',
              'Status lines are unstructured candidates, not validated player-game records',
              'No historical as-of authorization or training promotion']}
    (output_dir/(sha+'.audit.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
