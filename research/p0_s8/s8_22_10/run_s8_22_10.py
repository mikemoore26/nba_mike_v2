"""S8.22.10 manual official NBA injury-report PDF intake; no network access."""
import argparse
import hashlib
import json
import re
import shutil
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

GAME_TIPOFFS = {
    'DAL@WAS':'2023-11-16T00:00:00+00:00',
    'NYK@ATL':'2023-11-16T00:30:00+00:00',
    'BOS@PHI':'2023-11-16T00:30:00+00:00',
    'MIL@TOR':'2023-11-16T00:30:00+00:00',
    'ORL@CHI':'2023-11-16T01:00:00+00:00',
    'MIN@PHX':'2023-11-16T02:00:00+00:00',
    'SAC@LAL':'2023-11-16T03:00:00+00:00',
    'CLE@POR':'2023-11-16T03:00:00+00:00',
}
EDITION = re.compile(r'Injury\s+Report\s*:\s*(\d{1,2}/\d{1,2}/\d{2,4})\s+(\d{1,2}:\d{2})\s*(AM|PM)', re.I)
VALID_STATUSES = ('OUT', 'QUESTIONABLE', 'DOUBTFUL', 'PROBABLE', 'AVAILABLE')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def edition_from_text(text):
    m = EDITION.search(text[:2000])
    if not m:
        return None
    naive = datetime.strptime(' '.join(m.groups()), '%m/%d/%y %I:%M %p') if len(m.group(1).split('/')[-1]) == 2 else datetime.strptime(' '.join(m.groups()), '%m/%d/%Y %I:%M %p')
    return naive.replace(tzinfo=ZoneInfo('America/New_York')).astimezone(timezone.utc)


def inspect_pdf(data, cutoff_minutes=60):
    if not data.startswith(b'%PDF-'):
        raise ValueError('Not a PDF header')
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError('Install pypdf in your venv: python -m pip install pypdf') from exc
    import io
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        raise ValueError('Encrypted PDF not supported')
    text = '\n'.join(page.extract_text() or '' for page in reader.pages)
    edition = edition_from_text(text)
    if edition is None:
        raise ValueError('Cannot verify report edition timestamp from PDF text; review manually')
    edition_iso = edition.isoformat()
    games = []
    for matchup, tipoff_str in GAME_TIPOFFS.items():
        tipoff = datetime.fromisoformat(tipoff_str)
        cutoff = tipoff - timedelta(minutes=cutoff_minutes)
        # Edition label is a claimed publication time, not verified public availability.
        games.append({'matchup':matchup, 'tipoff_utc':tipoff_str, 'cutoff_utc':cutoff.isoformat(),
                      'edition_before_cutoff':edition <= cutoff,
                      'matchup_text_present': bool(re.search(re.escape(matchup).replace('\\@', r'\s*@\s*'), text))})
    return {'edition_label_utc':edition_iso, 'pages':len(reader.pages),
            'text_chars':len(text), 'status_mentions':{s:len(re.findall(r'\b'+s+r'\b',text,re.I)) for s in VALID_STATUSES},
            'games':games, 'text_extractable':bool(text.strip())}


def run(args):
    project = Path(args.project_root).resolve()
    source = Path(args.pdf).resolve()
    if not source.is_file():
        raise ValueError('Source PDF missing')
    if not args.source_url.startswith('https://'):
        raise ValueError('Source URL must be HTTPS and reflect the exact downloaded PDF')
    if not ('nba.com/' in args.source_url.lower().split('/')[2] or args.source_url.lower().split('/')[2].endswith('.nba.com')):
        raise ValueError('Source URL must be on an NBA domain; do not invent URLs')
    data = source.read_bytes()
    if len(data) > 30_000_000:
        raise ValueError('PDF exceeds 30MB intake limit')
    details = inspect_pdf(data, args.cutoff_minutes)
    retrieved = datetime.fromisoformat(args.retrieved_utc.replace('Z','+00:00'))
    if retrieved.tzinfo is None:
        raise ValueError('Retrieval timestamp must include timezone')
    # Local archive receipt attests present-day bytes, not 2023 historical publication.
    base = project / 'research/p0_s8/s8_22_10/evidence/2023-11-15' / uuid.uuid4().hex
    base.mkdir(parents=True, exist_ok=False)
    archived = base / 'source.pdf'
    archived.write_bytes(data)
    report = {
        'milestone':'S8.22.10', 'target_date':'2023-11-15', 'source_url':args.source_url,
        'retrieved_utc':retrieved.astimezone(timezone.utc).isoformat(),
        'sha256':sha256(data), 'bytes':len(data), 'source_file':str(archived.relative_to(project)),
        'report_type':'OFFICIAL_PDF_EDITION_LABEL_REVIEW', 'edition':details,
        'source_integrity':'PASS', 'edition_label_authenticated':'NOT_ESTABLISHED',
        'historical_public_availability':'NOT_CERTIFIED',
        'player_level_extraction':'NOT_VALIDATED',
        'eligibility_inference':'FORBIDDEN',
        'decision':'BLOCK_TRAINING',
        'issues':[],
        'next_action':'Manually verify PDF edition identity and timestamp against original NBA archive; review player rows and team non-submissions; do not treat unlisted players as available.'
    }
    (base/'receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('ARCHIVED:',base)
    print('PDF SHA256:',report['sha256'])
    print('EDITION LABEL UTC:',details['edition_label_utc'])
    print('BEFORE 60-MIN CUTOFF:',sum(g['edition_before_cutoff'] for g in details['games']),'of 8' if args.cutoff_minutes==60 else 'of 8 (custom cutoff)')
    print('HISTORICAL AS-OF: NOT_CERTIFIED')
    print('DECISION: BLOCK_TRAINING')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',default='.')
    p.add_argument('--pdf',required=True)
    p.add_argument('--source-url',required=True)
    p.add_argument('--retrieved-utc',required=True)
    p.add_argument('--cutoff-minutes',type=int,default=60)
    a=p.parse_args()
    if a.cutoff_minutes < 0 or a.cutoff_minutes > 1440:
        p.error('cutoff-minutes must be 0..1440')
    try:
        run(a)
    except Exception as exc:
        print('FAIL CLOSED:',str(exc),file=sys.stderr)
        sys.exit(2)

if __name__=='__main__':main()
