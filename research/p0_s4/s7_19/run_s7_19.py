"""S7.19: evidence-preserving NBA injury PDF as-of provenance audit.

No HTTP fetch, inferred timestamps, training data modifications, or approvals.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

STAMP = re.compile(r'Injury-Report_(\d{4}-\d{2}-\d{2})_(\d{2})_(\d{2})(AM|PM)\.pdf', re.I)


def audit_pdf(path: Path) -> dict:
    import pymupdf
    data = path.read_bytes()
    if not data.startswith(b'%PDF-'):
        raise ValueError(f'Not a PDF: {path}')
    sha = hashlib.sha256(data).hexdigest()
    with pymupdf.open(stream=data, filetype='pdf') as doc:
        metadata = doc.metadata or {}
        pages = len(doc)
        first_page = doc[0].get_text()[:1500] if pages else ''
    creation = (metadata.get('creationDate') or '').strip()
    modification = (metadata.get('modDate') or '').strip()
    return {
        'source_sha256': sha, 'filename': path.name, 'pages': pages,
        'pdf_creation_date_raw': creation, 'pdf_modification_date_raw': modification,
        'pdf_internal_timestamp_present': bool(creation or modification),
        'report_header_present': 'injury' in first_page.lower(),
        'historical_publication_verified': False,
        'eligible_for_asof_training': False,
        'decision': 'BLOCK_TRAINING',
        'reason': 'No independently verified contemporaneous publication evidence; PDF metadata cannot alone prove public availability',
    }


def audit_directory(pdf_dir: Path) -> dict:
    pdfs = sorted(pdf_dir.glob('*.pdf'))
    if not pdfs:
        raise ValueError(f'No PDFs in {pdf_dir}')
    reports = [audit_pdf(p) for p in pdfs]
    hashes = [r['source_sha256'] for r in reports]
    return {
        'milestone': 'S7.19', 'status': 'RESEARCH_ONLY', 'decision': 'BLOCK_TRAINING',
        'pdf_count': len(reports), 'distinct_hashes': len(set(hashes)),
        'pdfs_with_internal_timestamp': sum(r['pdf_internal_timestamp_present'] for r in reports),
        'historical_publication_verified': False,
        'eligible_for_asof_training': False,
        'reports': reports,
        'evidence_needed': [
            'Independent archived capture or timestamped contemporaneous record of public availability',
            'Authenticated capture time and exact URL or cryptographic content match',
            'Evidence timestamp strictly earlier than each modeled prediction cutoff',
            'Source versioning and later report revisions assessed separately',
        ],
        'limitations': [
            'PDF internal timestamps, when present, do not prove public publication time',
            'Filename timestamps are report labels, not verified availability',
            'Current HTTP response headers do not prove historical availability',
            'This audit does not verify player/team/matchup correctness',
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--pdf-dir', type=Path, default=Path('research/p0_s4/s7_14/input_pdfs'))
    p.add_argument('--output-dir', type=Path, default=Path('research/p0_s4/s7_19/results'))
    args = p.parse_args()
    report = audit_directory(args.pdf_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/'s7_19_report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    fields = ['source_sha256','filename','pages','pdf_creation_date_raw','pdf_modification_date_raw','pdf_internal_timestamp_present','report_header_present','historical_publication_verified','eligible_for_asof_training','decision','reason']
    with (args.output_dir/'s7_19_pdf_evidence.csv').open('w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader(); w.writerows(report['reports'])
    print(json.dumps({k:v for k,v in report.items() if k not in ('reports','evidence_needed','limitations')},indent=2))

if __name__ == '__main__':
    main()
