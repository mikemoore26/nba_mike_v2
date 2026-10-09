"""S7.45 offline reconciliation of S7.44 self-reported publication metadata."""
import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

REQUIRED = {'article_sha256','article_url','metadata_field','metadata_raw_value','metadata_normalized_date','metadata_source','historical_publication_verified','origin_team_verified','player_name','candidate_number'}
FIELDS = ['article_sha256','article_url','player_names','candidate_numbers','metadata_rows','distinct_candidate_dates','publication_dates','modified_dates','created_dates','unattributed_dates','preferred_publication_candidate','publication_candidate_basis','publication_conflict','modified_before_publication','unattributed_date_noise','archive_priority','review_status','quality_flags','historical_publication_verified','event_date_verified','independent_report_verified','eligible_for_asof_training']
PUB = {'datepublished','article:published_time','pubdate','publishdate','published','dc.date.issued','parsely-pub-date','sailthru.date'}
MOD = {'datemodified','article:modified_time'}
CREATED = {'datecreated'}

def category(field, source):
    key = field.lower().strip()
    if source == 'HTML_TIME_TEXT' or key.startswith('time.'):
        return 'unattributed'
    if key in PUB:
        return 'publication'
    if key in MOD:
        return 'modified'
    if key in CREATED:
        return 'created'
    return 'unattributed'

def parse_date(value):
    if not value:
        return ''
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Invalid normalized date: '+value)
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError('Invalid normalized date: '+value) from exc

def reconcile(rows):
    if not rows:
        raise ValueError('Empty S7.44 metadata review')
    grouped = defaultdict(list)
    for row in rows:
        if row['historical_publication_verified'].strip().lower() != 'false' or row['origin_team_verified'].strip().lower() != 'false':
            raise ValueError('Upstream verification flag must remain false')
        sha = row['article_sha256']
        if not re.fullmatch(r'[a-f0-9]{64}', sha):
            raise ValueError('Invalid article SHA256')
        u = urlsplit(row['article_url'])
        if u.scheme != 'https' or u.hostname not in ('nba.com','www.nba.com') or u.username or u.password or u.port not in (None,443):
            raise ValueError('Non-official article URL')
        parse_date(row['metadata_normalized_date'].strip())
        grouped[sha].append(row)
    out = []
    for sha, group in sorted(grouped.items()):
        urls = {r['article_url'] for r in group}
        if len(urls) != 1:
            raise ValueError('SHA256 mapped to multiple article URLs')
        dates = {k:set() for k in ('publication','modified','created','unattributed')}
        for r in group:
            d = r['metadata_normalized_date'].strip()
            if d:
                dates[category(r['metadata_field'],r['metadata_source'])].add(d)
        pub,mod,created,other = (sorted(dates[k]) for k in ('publication','modified','created','unattributed'))
        all_dates = sorted(set().union(*dates.values()))
        conflict = len(pub) > 1
        preferred = pub[0] if len(pub) == 1 else ''
        modified_before = bool(pub and mod and min(mod) < min(pub))
        flags = ['SELF_REPORTED_ONLY','HISTORICAL_AVAILABILITY_UNVERIFIED']
        if conflict: flags.append('PUBLICATION_FIELDS_CONFLICT')
        if modified_before: flags.append('MODIFICATION_PREDATES_PUBLICATION_CANDIDATE')
        if len(all_dates) > 1: flags.append('MULTIPLE_DISTINCT_DATES')
        if other: flags.append('UNATTRIBUTED_DATE_PRESENT')
        if not pub: flags.append('NO_EXPLICIT_PUBLICATION_DATE')
        if conflict or modified_before: priority='HIGH_CONFLICT_REVIEW'
        elif preferred: priority='HIGH_ARCHIVE_LOOKUP'
        elif created: priority='MEDIUM_ARCHIVE_LOOKUP'
        else: priority='LOW_INSUFFICIENT_PUBLICATION_SIGNAL'
        out.append({
            'article_sha256':sha,'article_url':next(iter(urls)),
            'player_names':';'.join(sorted({r['player_name'] for r in group if r['player_name']})),
            'candidate_numbers':';'.join(sorted({r['candidate_number'] for r in group if r['candidate_number']},key=lambda x:(not x.isdigit(),int(x) if x.isdigit() else x))),
            'metadata_rows':len(group),'distinct_candidate_dates':len(all_dates),
            'publication_dates':';'.join(pub),'modified_dates':';'.join(mod),
            'created_dates':';'.join(created),'unattributed_dates':';'.join(other),
            'preferred_publication_candidate':preferred,
            'publication_candidate_basis':'SINGLE_EXPLICIT_SELF_REPORTED_PUBLICATION_DATE' if preferred else 'NONE',
            'publication_conflict':str(conflict).lower(),'modified_before_publication':str(modified_before).lower(),
            'unattributed_date_noise':str(bool(other)).lower(),'archive_priority':priority,
            'review_status':'RECONCILED_CANDIDATE_REVIEW_ONLY','quality_flags':';'.join(flags),
            'historical_publication_verified':'false','event_date_verified':'false',
            'independent_report_verified':'false','eligible_for_asof_training':'false'
        })
    return sorted(out,key=lambda r:({'HIGH_CONFLICT_REVIEW':0,'HIGH_ARCHIVE_LOOKUP':1,'MEDIUM_ARCHIVE_LOOKUP':2,'LOW_INSUFFICIENT_PUBLICATION_SIGNAL':3}[r['archive_priority']],r['article_url']))

def run(review_csv,output_dir):
    with Path(review_csv).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            raise ValueError('S7.44 schema mismatch')
        source=list(reader)
    review=reconcile(source)
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    with (out/'s7_45_review.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(review)
    report={'milestone':'S7.45','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING',
            'input_metadata_rows':len(source),'unique_articles':len(review),
            'articles_with_multiple_distinct_dates':sum(int(r['distinct_candidate_dates']>1) for r in review),
            'articles_with_explicit_publication_candidates':sum(bool(r['publication_dates']) for r in review),
            'articles_with_publication_field_conflicts':sum(r['publication_conflict']=='true' for r in review),
            'articles_with_modified_before_publication':sum(r['modified_before_publication']=='true' for r in review),
            'archive_priority_counts':dict(sorted(Counter(r['archive_priority'] for r in review).items())),
            'historical_publication_verified':False,'event_dates_verified':0,'event_identity_resolved':0,
            'independent_reports_verified':0,'eligible_for_asof_training':False,
            'limitations':['Only S7.44 extracted metadata is reconciled; no new external historical evidence',
                           'A preferred publication candidate is not an independently verified publication date',
                           'A modification date or HTML time text must not substitute for publication evidence',
                           'No transaction chronology, roster, or training promotion']}
    (out/'s7_45_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--review-csv',default='research/p0_s4/s7_44/results/s7_44_review.csv')
    p.add_argument('--output-dir',default='research/p0_s4/s7_45/results')
    a=p.parse_args()
    try:print(json.dumps(run(a.review_csv,a.output_dir),indent=2))
    except (ValueError,OSError) as e:
        print(json.dumps({'milestone':'S7.45','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(e)}));raise SystemExit(1)
if __name__=='__main__':main()
