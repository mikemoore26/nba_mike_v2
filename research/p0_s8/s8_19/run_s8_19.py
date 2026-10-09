"""S8.19 offline publication-metadata and independent-capture evidence intake.
No source is certified by this script. No network, training or betting.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from html.parser import HTMLParser

TIPOFF = datetime.fromisoformat('2023-10-24T19:30:00-04:00')
PRIORITY = {'denver_team_preview', 'nba_0630_report'}

class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = []
        self.times = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag.lower() == 'meta':
            key = a.get('property') or a.get('name') or a.get('itemprop') or ''
            val = a.get('content') or ''
            if any(w in key.lower() for w in ('date', 'time', 'publish', 'modify', 'update')):
                self.meta.append((key[:100], val[:200]))
        if tag.lower() == 'time':
            self.times.append(a.get('datetime', '')[:200])

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def safe_repo_path(root, value):
    p = (root / value.replace('\\', '/')).resolve()
    if not p.is_relative_to(root.resolve()):
        raise ValueError('path escapes project root')
    return p

def extract_claims(path):
    raw = path.read_bytes()
    if raw.startswith(b'%PDF-'):
        matches = re.findall(rb'/((?:CreationDate|ModDate))\s*\(([^)]{1,90})\)', raw)
        return 'PDF', [{'field': k.decode('ascii'), 'value': v.decode('latin1')} for k, v in matches][:30]
    if path.suffix.lower() in {'.html', '.htm'}:
        parser = MetaParser()
        parser.feed(raw.decode('utf-8', errors='replace'))
        claims = [{'field': k, 'value': v} for k, v in parser.meta[:50]]
        claims += [{'field': 'time.datetime', 'value': t} for t in parser.times[:20]]
        return 'HTML', claims
    return 'OTHER', []

def parse_capture_timestamp(value):
    try:
        v = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if v.tzinfo is None:
            return None
        return v.astimezone(timezone.utc)
    except (ValueError, AttributeError):
        return None

def read_csv(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)

def run(root):
    root = root.resolve()
    out = root / 'research/p0_s8/s8_19/results'
    out.mkdir(parents=True, exist_ok=True)
    source_audit = root / 'research/p0_s8/s8_18/results/s8_18_source_audit.csv'
    if not source_audit.exists():
        raise FileNotFoundError(f'Missing S8.18 source audit: {source_audit}')
    source_rows = read_csv(source_audit)
    candidates = [r for r in source_rows if r.get('source_id') in PRIORITY]
    if len(candidates) != 2:
        raise ValueError('Expected both priority source IDs in S8.18 audit')
    artifact_rows, claim_rows, issues = [], [], []
    for r in candidates:
        sid = r['source_id']
        rel = r.get('artifact_path', '')
        item = {'source_id': sid, 'artifact_path': rel, 'acquisition_status': r.get('retrieval_status', ''),
                'expected_sha256': r.get('sha256', ''), 'actual_sha256': '', 'integrity': 'NOT_CHECKED',
                'document_type': '', 'claim_count': 0, 'publication_verdict': 'UNVERIFIED'}
        if not rel:
            item['integrity'] = 'MISSING_PATH'
        else:
            try:
                p = safe_repo_path(root, rel)
                if not p.is_file():
                    item['integrity'] = 'ARTIFACT_NOT_PRESENT'
                else:
                    actual = sha256(p)
                    item['actual_sha256'] = actual
                    if not r.get('sha256') or actual.lower() != r['sha256'].lower():
                        item['integrity'] = 'HASH_MISMATCH_OR_MISSING_EXPECTED'
                    else:
                        item['integrity'] = 'MATCH'
                        typ, claims = extract_claims(p)
                        item['document_type'] = typ
                        item['claim_count'] = len(claims)
                        for claim in claims:
                            claim_rows.append({'source_id': sid, **claim, 'evidence_level': 'PUBLISHER_OR_FILE_CLAIM_ONLY'})
            except (OSError, ValueError) as exc:
                item['integrity'] = 'PATH_OR_READ_ERROR'
                issues.append({'source_id': sid, 'issue': str(exc)[:250]})
        artifact_rows.append(item)
    # Evidence intake: a timestamp and archived bytes may be provided, but the timestamp's
    # independent origin, replay identity and provenance require external manual validation.
    intake = root / 'research/p0_s8/s8_19/capture_intake.csv'
    capture_rows = []
    if intake.exists():
        for r in read_csv(intake):
            sid = r.get('source_id', '')
            stamp = parse_capture_timestamp(r.get('capture_timestamp_utc', ''))
            status = 'UNVERIFIED'
            note = 'Archive index claim alone is insufficient'
            if sid not in PRIORITY:
                status, note = 'REJECTED', 'Unknown source ID'
            elif stamp is None:
                status, note = 'REJECTED', 'Missing or invalid timezone-aware capture timestamp'
            elif stamp >= TIPOFF.astimezone(timezone.utc):
                status, note = 'POST_TIPOFF', 'Capture timestamp at/after scheduled tipoff'
            else:
                status, note = 'CANDIDATE_PRE_TIPOFF_CAPTURE', 'Requires independent replay, timestamp and identity verification'
            rel = r.get('capture_artifact_path', '')
            integrity = 'NOT_PROVIDED'
            if rel:
                try:
                    p = safe_repo_path(root, rel)
                    if p.is_file():
                        actual = sha256(p)
                        integrity = 'MATCH' if r.get('capture_sha256') and actual.lower() == r['capture_sha256'].lower() else 'HASH_MISMATCH_OR_MISSING_EXPECTED'
                    else:
                        integrity = 'ARTIFACT_NOT_PRESENT'
                except (OSError, ValueError):
                    integrity = 'PATH_OR_READ_ERROR'
            capture_rows.append({'source_id': sid, 'capture_timestamp_utc': r.get('capture_timestamp_utc', ''),
                                 'archive_url': r.get('archive_url', ''), 'capture_artifact_path': rel,
                                 'artifact_integrity': integrity, 'classification': status,
                                 'reason': note, 'independently_verified': False})
    write_csv(out / 's8_19_artifact_review.csv', artifact_rows,
              ['source_id','artifact_path','acquisition_status','expected_sha256','actual_sha256','integrity','document_type','claim_count','publication_verdict'])
    write_csv(out / 's8_19_publication_claims.csv', claim_rows, ['source_id','field','value','evidence_level'])
    write_csv(out / 's8_19_capture_review.csv', capture_rows,
              ['source_id','capture_timestamp_utc','archive_url','capture_artifact_path','artifact_integrity','classification','reason','independently_verified'])
    report = {'milestone':'S8.19', 'mode':'OFFLINE_PUBLICATION_METADATA_AND_CAPTURE_INTAKE',
              'sources_prioritized': len(candidates), 'artifacts_hash_verified':sum(r['integrity']=='MATCH' for r in artifact_rows),
              'publisher_metadata_claims':len(claim_rows),'capture_intake_rows':len(capture_rows),
              'independently_verified_captures':0,'independently_verified_games':0,
              'issues':issues,'verdict':'HISTORICAL_PUBLICATION_UNVERIFIED',
              'decision':'BLOCK_TRAINING','status':'RESEARCH_ONLY',
              'limitations':['Offline inspection cannot establish historical public availability',
                             'Publisher HTML metadata and PDF internal dates are claims, not independent capture timestamps',
                             'User-supplied archive metadata is not independent proof; replay and identity require external verification',
                             'Injury reports and team previews do not establish complete eligible player population',
                             '88 restart-period games remain separately blocked']}
    (out / 's8_19_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', default='.')
    args = parser.parse_args()
    run(Path(args.project_root))
