"""S7.46: independently timestamped archive capture discovery (research only)."""
import argparse
import csv
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
INPUT = ROOT / 'research/p0_s4/s7_45/results/s7_45_review.csv'
OUTPUT = Path(__file__).resolve().parent / 'results'
CDX = 'https://web.archive.org/cdx/search/cdx'
UA = 'NBA-MIKE-v2 research archive audit/1.0 (non-commercial)'
FIELDS = ['article_url','article_sha256','player_names','publication_candidate','archive_timestamp','archive_original_url','archive_status','archive_digest','archive_mimetype','archive_replay_url','capture_time_utc','archive_capture_status','url_match','claim_match','captured_sha256','review_status','historical_publication_verified','eligible_for_asof_training','error']

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def normalize_url(url):
    p = urlsplit(url.strip())
    return (p.netloc.lower().removeprefix('www.'), p.path.rstrip('/').lower())

def exact_url_match(a, b):
    return normalize_url(a) == normalize_url(b)

def valid_timestamp(ts):
    if not re.fullmatch(r'\d{14}', ts or ''):
        return False
    try:
        datetime.strptime(ts, '%Y%m%d%H%M%S')
        return True
    except ValueError:
        return False

def parse_cdx(raw):
    obj = json.loads(raw)
    if not isinstance(obj, list) or not obj:
        return []
    headers = obj[0]
    required = {'timestamp','original','statuscode','digest','mimetype'}
    if not isinstance(headers, list) or not required.issubset(headers):
        raise ValueError('CDX columns missing')
    rows = []
    for entry in obj[1:]:
        if not isinstance(entry, list) or len(entry) != len(headers):
            continue
        d = dict(zip(headers, entry))
        if valid_timestamp(d['timestamp']):
            rows.append(d)
    return rows

def fetch(url, timeout=20, max_bytes=4_000_000):
    request = Request(url, headers={'User-Agent': UA, 'Accept':'application/json,text/html,*/*'})
    with urlopen(request, timeout=timeout) as resp:
        data = resp.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError('Response exceeds byte limit')
        return data, resp.geturl()

def query_url(original):
    return CDX + '?url=' + quote(original, safe='') + '&output=json&filter=statuscode:200&collapse=timestamp:6&fl=timestamp,original,statuscode,digest,mimetype&filter=mimetype:text/html'

def replay_url(ts, original):
    return f'https://web.archive.org/web/{ts}id_/{original}'

def strip_markup(blob):
    txt = blob.decode('utf-8', 'replace')
    txt = re.sub(r'(?is)<(script|style|noscript)\b[^>]*>.*?</\1>', ' ', txt)
    txt = re.sub(r'(?s)<[^>]+>', ' ', txt)
    return re.sub(r'\s+', ' ', txt).casefold()

def check_claim(blob, players):
    text = strip_markup(blob)
    names = [x.strip().casefold() for x in (players or '').split(';') if x.strip()]
    # Player mention alone is NOT enough to verify a transaction claim.
    return 'PLAYER_MENTION_ONLY' if names and any(n in text for n in names) else 'NO_PLAYER_MENTION'

def process(input_path=INPUT, output_dir=OUTPUT, offline=False, fetch_captures=False, sleep_seconds=1.0):
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(input_path, encoding='utf-8-sig', newline='') as f:
        sources = list(csv.DictReader(f))
    records = []
    raw_dir = output_dir / 'archive_objects'
    if fetch_captures:
        raw_dir.mkdir(exist_ok=True)
    for source in sources:
        url = source.get('article_url','')
        if urlsplit(url).scheme != 'https' or not urlsplit(url).netloc.endswith('nba.com'):
            raise ValueError('Only HTTPS nba.com article URLs are permitted')
        base = dict.fromkeys(FIELDS, '')
        base.update(article_url=url,article_sha256=source.get('article_sha256',''),player_names=source.get('player_names',''),publication_candidate=source.get('preferred_publication_candidate',''),historical_publication_verified='false',eligible_for_asof_training='false')
        if offline:
            records.append(dict(base,archive_capture_status='NOT_QUERIED_OFFLINE',review_status='UNRESOLVED'))
            continue
        try:
            data, _ = fetch(query_url(url))
            candidates = [r for r in parse_cdx(data) if exact_url_match(url,r['original']) and r['statuscode']=='200' and r['mimetype'].startswith('text/html')]
            if not candidates:
                records.append(dict(base,archive_capture_status='NO_EXACT_ARCHIVE_CAPTURE_FOUND',review_status='UNRESOLVED'))
            for candidate in candidates:
                ts = candidate['timestamp']
                rurl = replay_url(ts, candidate['original'])
                rec = dict(base, archive_timestamp=ts,archive_original_url=candidate['original'],archive_status=candidate['statuscode'],archive_digest=candidate['digest'],archive_mimetype=candidate['mimetype'],archive_replay_url=rurl,capture_time_utc=datetime.strptime(ts,'%Y%m%d%H%M%S').replace(tzinfo=timezone.utc).isoformat(),url_match='EXACT_PATH_HOST',archive_capture_status='INDEX_ONLY',claim_match='NOT_CHECKED',review_status='ARCHIVE_INDEX_REVIEW_ONLY')
                if fetch_captures:
                    try:
                        blob, effective = fetch(rurl)
                        # Archive replay can redirect; never silently accept a different URL.
                        if not effective.startswith(f'https://web.archive.org/web/{ts}'):
                            raise ValueError('Unexpected archive replay redirect')
                        digest = sha256(blob)
                        (raw_dir / (digest + '.html')).write_bytes(blob)
                        rec.update(captured_sha256=digest,claim_match=check_claim(blob,source.get('player_names','')),archive_capture_status='CAPTURE_SAVED_SHA256',review_status='CAPTURE_CONTENT_REVIEW_REQUIRED')
                    except Exception as e:
                        rec.update(archive_capture_status='CAPTURE_FETCH_FAILED',error=str(e)[:240],review_status='UNRESOLVED')
                records.append(rec)
            time.sleep(max(0,sleep_seconds))
        except Exception as e:
            records.append(dict(base,archive_capture_status='CDX_QUERY_FAILED',review_status='UNRESOLVED',error=str(e)[:240]))
    with open(output_dir/'s7_46_review.csv','w',encoding='utf-8',newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS);w.writeheader();w.writerows(records)
    counts = {}
    for r in records:
        s=r['archive_capture_status'];counts[s]=counts.get(s,0)+1
    report = {'milestone':'S7.46','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','article_urls':len(sources),'review_rows':len(records),'archive_status_counts':counts,'archive_index_candidates':sum(r['archive_capture_status'] in ('INDEX_ONLY','CAPTURE_SAVED_SHA256','CAPTURE_FETCH_FAILED') for r in records),'historical_publication_verified':False,'event_dates_verified':0,'independent_reports_verified':0,'eligible_for_asof_training':False,'limitations':['CDX index timestamp is archive-reported and not independently attested in this workflow','Archive index does not establish archived transaction claim','Player mention alone is not evidence of transaction direction','A capture only establishes possible availability by capture time, not claimed publication time','No transaction or roster evidence promotion']}
    (output_dir/'s7_46_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=INPUT)
    p.add_argument('--output-dir',type=Path,default=OUTPUT)
    p.add_argument('--offline',action='store_true',help='Produce a dry-run inventory without network calls')
    p.add_argument('--fetch-captures',action='store_true',help='Also download matching archived HTML for manual review')
    p.add_argument('--sleep-seconds',type=float,default=1.0)
    a=p.parse_args()
    print(json.dumps(process(a.input,a.output_dir,a.offline,a.fetch_captures,a.sleep_seconds),indent=2))
if __name__=='__main__':
    main()
