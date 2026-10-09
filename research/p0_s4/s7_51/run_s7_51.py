"""S7.51 offline evidence bottleneck and stop/go decision. No training promotion."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = ROOT / 'research/p0_s4/s7_50/results/s7_50_review.csv'
DEFAULT_OUTPUT = Path(__file__).resolve().parent / 'results'


def canonical_url(url: str) -> str:
    try:
        p = urlsplit(url.strip())
        return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip('/'), '', '')) if p.scheme in ('https', 'http') and p.netloc else ''
    except ValueError:
        return ''


def category(row: dict) -> str:
    if row.get('mapping_status') != 'COMPLETE' or not row.get('player_name', '').strip():
        return 'MAPPING_GAP'
    if row.get('integrity_status') != 'SHA256_MATCH' or not row.get('captured_sha256', '').strip():
        return 'CAPTURE_UNAVAILABLE_OR_UNVERIFIED'
    direction = row.get('direction_status', '')
    if direction == 'FULL_TEXT_DIRECTION_CANDIDATE':
        return 'DIRECTION_CANDIDATE_UNVERIFIED'
    if direction == 'COOCCURRENCE_ONLY':
        return 'DIRECTION_NOT_ESTABLISHED'
    if direction == 'NO_PLAYER_IN_EXTRACTED_CONTENT':
        return 'PLAYER_NOT_RECOVERED'
    return 'CONTENT_OR_EXTRACTION_UNRESOLVED'


def priority(cat: str) -> str:
    return {
        'MAPPING_GAP': 'P1_MAPPING_FIX',
        'CAPTURE_UNAVAILABLE_OR_UNVERIFIED': 'P2_EXTERNAL_SOURCE_OR_CAPTURE',
        'DIRECTION_CANDIDATE_UNVERIFIED': 'P1_INDEPENDENT_TIMESTAMPED_CORROBORATION',
        'DIRECTION_NOT_ESTABLISHED': 'P2_SOURCE_REVIEW',
        'PLAYER_NOT_RECOVERED': 'P3_NO_MORE_SAME_OBJECT_EXTRACTION',
        'CONTENT_OR_EXTRACTION_UNRESOLVED': 'P3_NO_MORE_SAME_OBJECT_EXTRACTION',
    }[cat]


def audit(rows: list[dict], input_hash: str) -> tuple[dict, list[dict], list[dict]]:
    seen = set()
    objects = defaultdict(set)
    by_article = defaultdict(list)
    out = []
    for index, row in enumerate(rows, 1):
        url = canonical_url(row.get('article_url', ''))
        sha = row.get('captured_sha256', '').strip().lower()
        verified = row.get('integrity_status') == 'SHA256_MATCH' and len(sha) == 64 and all(c in '0123456789abcdef' for c in sha)
        if verified:
            objects[url].add(sha)
        if url:
            by_article[url].append(index)
        cat = category(row)
        identity = (url, sha if verified else '', row.get('player_name', '').strip(), row.get('origin_candidate', '').strip(), row.get('destination_candidate', '').strip(), row.get('direction_status', '').strip())
        duplicate = identity in seen
        seen.add(identity)
        out.append({
            'source_row': index, 'player_name': row.get('player_name', ''),
            'article_url': url, 'capture_sha256': sha if verified else '',
            'archive_timestamp': row.get('archive_timestamp', ''),
            'origin_candidate': row.get('origin_candidate', ''),
            'destination_candidate': row.get('destination_candidate', ''),
            'bottleneck': cat, 'recommended_action': priority(cat),
            'duplicate_player_claim_row': str(duplicate).lower(),
            'source_family': row.get('source_family', ''),
            'independent_corroboration_verified': 'false',
            'historical_asof_eligible': 'false',
        })
    cats = Counter(r['bottleneck'] for r in out)
    unique_verified_objects = {sha for shas in objects.values() for sha in shas}
    articles = []
    for url in sorted(by_article):
        associated = [out[i-1] for i in by_article[url]]
        articles.append({
            'article_url': url,
            'review_rows': len(associated),
            'unique_sha_verified_capture_objects': len(objects[url]),
            'distinct_named_players': len({r['player_name'] for r in associated if r['player_name']}),
            'direction_candidate_rows': sum(r['bottleneck'] == 'DIRECTION_CANDIDATE_UNVERIFIED' for r in associated),
            'source_independence_verified': 'false',
        })
    report = {
        'milestone': 'S7.51', 'status': 'RESEARCH_ONLY', 'decision': 'BLOCK_TRAINING',
        'input_rows': len(rows), 'review_rows': len(out),
        'bottleneck_counts': dict(sorted(cats.items())),
        'distinct_article_urls': len(by_article),
        'sha256_verified_unique_capture_objects': len(unique_verified_objects),
        'duplicate_player_claim_rows': sum(r['duplicate_player_claim_row'] == 'true' for r in out),
        'direction_candidate_rows': cats['DIRECTION_CANDIDATE_UNVERIFIED'],
        'verified_independent_source_families': 0,
        'historical_publication_verified': False,
        'event_dates_verified': 0,
        'eligible_for_asof_training': False,
        'input_csv_sha256': input_hash,
        'research_track_decision': 'PAUSE_REPEATED_ARCHIVE_EXTRACTION',
        'next_research_dependency': 'INDEPENDENT_TIMESTAMPED_TRANSACTION_OR_ROSTER_SOURCE',
        'parallel_work_allowed': 'ONLY_INDEPENDENTLY_VALIDATED_NON_ROSTER_COMPONENTS',
        'stop_conditions': [
            'Do not repeat same archived HTML extraction without a falsifiable new method and expected yield.',
            'Do not promote URL slug, index timestamp, SHA match or single article to historical publication proof.',
            'Reopen chronology only with new independently timestamped transaction/roster evidence or a demonstrable mapping fix.',
            'Historical as-of roster/transaction features remain excluded from training and evaluation.',
        ],
        'limitations': [
            'Input is the S7.50 review CSV, not a complete inventory of all NBA transactions.',
            'SHA-256 values are upstream verification labels; S7.51 does not rehash original archive files.',
            'Rows and article captures are not independent evidence units.',
            'No network requests or claims of independent timestamp attestation.',
        ],
    }
    assert sum(cats.values()) == len(rows)
    return report, out, articles


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DEFAULT_INPUT)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    raw = args.input.read_bytes()
    with args.input.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        required = {'article_url','player_name','mapping_status','integrity_status','captured_sha256','direction_status'}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f'S7.50 input missing required columns: {sorted(missing)}')
        rows = list(reader)
    report, review, articles = audit(rows, hashlib.sha256(raw).hexdigest())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 's7_51_report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    write_csv(args.output_dir / 's7_51_review.csv', review, list(review[0]) if review else ['source_row','bottleneck'])
    write_csv(args.output_dir / 's7_51_article_inventory.csv', articles, list(articles[0]) if articles else ['article_url'])
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report

if __name__ == '__main__':
    main()
